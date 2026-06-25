import csv
import datetime
from dataclasses import dataclass
from typing import List, Tuple, Dict, Iterable


@dataclass(frozen=True)
class CostMetric:
    """Cost metric for a given day and service."""
    date: datetime.date
    service: str
    memory_gb_hour: float
    cost_usd: float


@dataclass(frozen=True)
class MemorySnapshot:
    """Memory usage snapshot for a given day."""
    date: datetime.date
    memory_gb: float


def parse_cost_metrics(csv_text: str) -> List[CostMetric]:
    """
    Parse CSV text containing cost metrics.

    Expected header: date,service,memory_gb_hour,cost_usd
    Date format: YYYY-MM-DD
    """
    reader = csv.DictReader(csv_text.strip().splitlines())
    metrics: List[CostMetric] = []
    for row in reader:
        try:
            date = datetime.datetime.strptime(row["date"], "%Y-%m-%d").date()
            service = row["service"]
            memory_gb_hour = float(row["memory_gb_hour"])
            cost_usd = float(row["cost_usd"])
        except (KeyError, ValueError) as exc:
            raise ValueError(f"Invalid row in cost metrics CSV: {row}") from exc
        metrics.append(CostMetric(date, service, memory_gb_hour, cost_usd))
    return metrics


def compute_memory_increase(
    snapshots: List[MemorySnapshot],
) -> List[Tuple[datetime.date, float]]:
    """
    Compute daily memory increase (delta) compared to the previous day.

    Returns a list of (date, delta_gb). The first day delta is 0.
    """
    if not snapshots:
        return []

    # Ensure snapshots are sorted by date
    snapshots = sorted(snapshots, key=lambda s: s.date)
    result: List[Tuple[datetime.date, float]] = []
    previous = snapshots[0].memory_gb
    result.append((snapshots[0].date, 0.0))

    for snap in snapshots[1:]:
        delta = snap.memory_gb - previous
        result.append((snap.date, delta))
        previous = snap.memory_gb
    return result


def estimate_incremental_cost(
    increments: List[Tuple[datetime.date, float]],
    cost_per_gb_hour: float,
) -> List[Tuple[datetime.date, float]]:
    """
    Convert memory increments into incremental cost.

    cost_per_gb_hour is the USD cost for one GB of memory per hour.
    The function assumes a 24‑hour day for each increment.
    """
    result: List[Tuple[datetime.date, float]] = []
    for date, delta_gb in increments:
        incremental_cost = max(delta_gb, 0.0) * 24.0 * cost_per_gb_hour
        result.append((date, incremental_cost))
    return result


def generate_time_series(
    cost_metrics: List[CostMetric],
    memory_increments: List[Tuple[datetime.date, float]],
    leak_threshold_gb: float = 0.5,
) -> List[Tuple[datetime.date, float, float, bool]]:
    """
    Produce a time‑series for the last 30 days.

    Each entry is (date, total_cost_usd, incremental_cost_usd, is_leak).
    - total_cost_usd: sum of cost_usd for that date across services.
    - incremental_cost_usd: cost derived from memory increase.
    - is_leak: True if the memory delta exceeds leak_threshold_gb.
    """
    # Build lookup tables
    cost_by_date: Dict[datetime.date, float] = {}
    for metric in cost_metrics:
        cost_by_date.setdefault(metric.date, 0.0)
        cost_by_date[metric.date] += metric.cost_usd

    inc_by_date: Dict[datetime.date, Tuple[float, bool]] = {}
    for date, delta in memory_increments:
        inc_by_date[date] = (delta, delta > leak_threshold_gb)

    # Determine the date range (last 30 days from the latest metric)
    if cost_metrics:
        latest = max(metric.date for metric in cost_metrics)
    elif memory_increments:
        latest = max(date for date, _ in memory_increments)
    else:
        return []

    start = latest - datetime.timedelta(days=29)
    series: List[Tuple[datetime.date, float, float, bool]] = []
    for i in range(30):
        day = start + datetime.timedelta(days=i)
        total_cost = cost_by_date.get(day, 0.0)
        delta, is_leak = inc_by_date.get(day, (0.0, False))
        incremental_cost = max(delta, 0.0) * 24.0 * _average_cost_per_gb_hour(cost_metrics)
        series.append((day, total_cost, incremental_cost, is_leak))
    return series


def _average_cost_per_gb_hour(cost_metrics: Iterable[CostMetric]) -> float:
    """
    Helper to compute average cost per GB‑hour from provided metrics.
    Returns 0.0 if no data is available.
    """
    total_cost = 0.0
    total_gb_hour = 0.0
    for metric in cost_metrics:
        total_cost += metric.cost_usd
        total_gb_hour += metric.memory_gb_hour
    if total_gb_hour == 0.0:
        return 0.0
    return total_cost / total_gb_hour


def export_to_csv(
    series: List[Tuple[datetime.date, float, float, bool]]
) -> str:
    """
    Export the time‑series to a CSV string.

    Columns: date,total_cost_usd,incremental_cost_usd,is_leak
    """
    output = ["date,total_cost_usd,incremental_cost_usd,is_leak"]
    for date, total, inc, leak in series:
        line = f"{date.isoformat()},{total:.2f},{inc:.2f},{leak}"
        output.append(line)
    return "\n".join(output)
