import textwrap

import pytest

from memory_sweeper import detect_leaks, LeakReport


def test_open_without_close_reports_high_severity():
    src = textwrap.dedent(
        """
        f = open('data.txt')
        data = f.read()
        """
    )
    reports = detect_leaks(src)
    assert len(reports) == 1
    report = reports[0]
    assert isinstance(report, LeakReport)
    assert report.severity == "high"
    assert "File opened without guaranteed close" in report.message
    assert "with open('path') as f" in report.suggestion
    assert report.line == 2  # line where open() call occurs


def test_open_inside_with_is_not_reported():
    src = textwrap.dedent(
        """
        with open('data.txt') as f:
            data = f.read()
        """
    )
    reports = detect_leaks(src)
    assert reports == []


def test_open_then_close_is_not_reported():
    src = textwrap.dedent(
        """
        f = open('data.txt')
        data = f.read()
        f.close()
        """
    )
    reports = detect_leaks(src)
    assert reports == []


def test_socket_without_close_reports_medium_severity():
    src = textwrap.dedent(
        """
        import socket
        s = socket.socket()
        s.connect(('example.com', 80))
        """
    )
    reports = detect_leaks(src)
    assert len(reports) == 1
    report = reports[0]
    assert report.severity == "medium"
    assert "Socket created without guaranteed close" in report.message
    assert "with socket.socket() as s" in report.suggestion
    assert report.line == 3  # line where socket.socket() call occurs


def test_socket_inside_with_is_not_reported():
    src = textwrap.dedent(
        """
        import socket
        with socket.socket() as s:
            s.connect(('example.com', 80))
        """
    )
    reports = detect_leaks(src)
    assert reports == []


def test_multiple_issues_reported_separately():
    src = textwrap.dedent(
        """
        f = open('a.txt')
        s = socket.socket()
        # no close for either
        """
    )
    reports = detect_leaks(src)
    # Expect two reports: one high (file) and one medium (socket)
    severities = {r.severity for r in reports}
    assert severities == {"high", "medium"}
    # Ensure both lines are captured
    lines = {r.line for r in reports}
    assert lines == {2, 3}
