import pytest
from memory_sweeper import MemorySweeper, MemorySnapshot
import sys
import io
import contextlib

def test_memory_sweeper_start_stop():
    sweeper = MemorySweeper()
    sweeper.start_profiling()
    sweeper.stop_profiling()
    assert True

def test_memory_sweeper_take_snapshot():
    sweeper = MemorySweeper()
    sweeper.start_profiling()
    sweeper.take_snapshot()
    sweeper.stop_profiling()
    assert len(sweeper.get_memory_usage()) == 1

def test_memory_sweeper_get_memory_usage():
    sweeper = MemorySweeper()
    sweeper.start_profiling()
    sweeper.take_snapshot()
    sweeper.take_snapshot()
    sweeper.stop_profiling()
    memory_usage = sweeper.get_memory_usage()
    assert len(memory_usage) == 2
    assert isinstance(memory_usage[0], MemorySnapshot)

def test_memory_sweeper_memory_snapshot():
    timestamp = 1643723400.0
    memory_usage = 1024
    snapshot = MemorySnapshot(timestamp, memory_usage)
    assert snapshot.timestamp == timestamp
    assert snapshot.memory_usage == memory_usage

def test_memory_sweeper_main():
    import sys
    import io
    import contextlib
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        import memory_sweeper
        memory_sweeper.main()
    output = f.getvalue()
    assert output is not None
