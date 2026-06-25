import datetime
import textwrap

import pytest

from memory_sweeper import (
    CostMetric,
    MemorySnapshot,
    parse_cost_metrics,
    compute_memory_increase,
    estimate_incremental_cost,
    generate_time_series,
    export_to_csv,
)


def test_parse_cost_metrics_happy_path():
    csv_data = textwrap.dedent(
        """
        date,service,memory_gb_hour,cost_usd
        2023-01-01,ec2,120.0,24.0
        2023-01-01,rds,80.0,16.0
        """
    )
    metrics = parse_cost_metrics(csv_data)
    assert len(metrics) == 2
    assert metrics[0] == CostMetric(
        date=datetime.date(2023, 1, 1),
        service="ec2",
        memory_gb_hour=120.0,
        cost_usd=24.0,
    )
    assert metrics[1].service == "rds"


def test_parse_cost_metrics_invalid_row():
    csv_data = "date,service,memory_gb_hour,cost_usd\n2023-01-01,ec2,not_a_number,24.0"
    with pytest.raises(ValueError):
        parse_cost_metrics(csv_data)


def test_compute_memory_increase_happy_path():
    snapshots = [
        MemorySnapshot(date=datetime.date(2023, 1, 1), memory_gb=4.0),
        MemorySnapshot(date=datetime.date(2023, 1, 2), memory_gb=5.5),
        MemorySnapshot(date=datetime.date(2023, 1, 3), memory_gb=5.0),
    ]
    inc = compute_memory_increase(snapshots)
    expected = [
        (datetime.date(2023, 1, 1), 0.0),
        (datetime.date(2023, 1, 2), 1.5),
        (datetime.date(2023, 1, 3), -0.5),
    ]
    assert inc == expected


def test_compute_memory_increase_empty():
    assert compute_memory_increase([]) == []


def test_estimate_incremental_cost_happy_path():
    increments = [
        (datetime.date(2023, 1, 1), 1.0),
        (datetime.date(2023, 1, 2), 0.0),
        (datetime.date(2023, 1, 3), -0.5),
    ]
    cost_per_gb_hour = 0.01  # $0.01 per GB‑hour
    result = estimate_incremental_cost(increments, cost_per_gb_hour)
    expected = [
        (datetime.date(2023, 1, 1), 1.0 * 24 * 0.01),
        (datetime.date(2023, 1, 2), 0.0),
        (datetime.date(2023, 1, 3), 0.0),  # negative delta treated as 0
    ]
    assert result == expected


def test_generate_time_series_happy_path():
    # Cost metrics for three days
    cost_metrics = [
        CostMetric(
            date=datetime.date(2023, 1, 1),
            service="ec2",
            memory_gb_hour=100,
            cost_usd=20,
        ),
        CostMetric(
            date=datetime.date(2023, 1, 2),
            service="ec2",
            memory_gb_hour=120,
            cost_usd=24,
        ),
        CostMetric(
            date=datetime.date(2023, 1, 3),
            service="ec2",
            memory_gb_hour=80,
            cost_usd=16,
        ),
    ]

    # Memory increments (same dates)
    memory_increments = [
        (datetime.date(2023, 1, 1), 0.0),
        (datetime.date(2023, 1, 2), 1.0),  # leak candidate
        (datetime.date(2023, 1, 3), 0.2),
    ]

    series = generate_time_series(cost_metrics, memory_increments, leak_threshold_gb=0.5)
    # Only the last three days of the 30‑day window contain data
    last_three = series[-3:]

    # Verify total cost matches input
    assert last_three[0][1] == 20.0
    assert last_three[1][1] == 24.0
    assert last_three[2][1] == 16.0

    # Verify leak detection
    assert last_three[0][3] is False
    assert last_three[1][3] is True
    assert last_three[2][3] is False

    # Verify incremental cost is computed using average cost per GB‑hour
    avg_cost_per_gb_hour = (
        sum(m.cost_usd for m in cost_metrics) / sum(m.memory_gb_hour for m in cost_metrics)
    )
    expected_inc_day2 = 1.0 * 24 * avg_cost_per_gb_hour
    assert pytest.approx(last_three[1][2], rel=1e-6) == expected_inc_day2


def test_generate_time_series_missing_cost():
    # No cost metrics, only memory increments
    series = generate_time_series([], [(datetime.date(2023, 1, 1), 2.0)])
    # Should still produce a 30‑day series ending on 2023‑01‑01
    assert series[-1][0] == datetime.date(2023, 1, 1)
    # Total cost should be zero
    assert series[-1][1] == 0.0
    # Incremental cost should be based on average (which is zero) => zero
    assert series[-1][2] == 0.0
    # Leak flag should be True (2.0 > default 0.5)
    assert series[-1][3] is True


def test_export_to_csv():
    series = [
        (
            datetime.date(2023, 1, 1),
            20.0,
            5.0,
            False,
        ),
        (
            datetime.date(2023, 1, 2),
            24.0,
            10.0,
            True,
        ),
    ]
    csv_output = export_to_csv(series)
    lines = csv_output.splitlines()
    assert lines[0] == "date,total_cost_usd,incremental_cost_usd,is_leak"
    assert lines[1] == "2023-01-01,20.00,5.00,False"
    assert lines[2] == "2023-01-02,24.00,10.00,True"
