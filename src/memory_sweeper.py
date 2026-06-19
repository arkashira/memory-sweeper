import argparse
import json
import dataclasses
import tracemalloc
import time
import sys

@dataclasses.dataclass
class MemorySnapshot:
    timestamp: float
    memory_usage: int

class MemorySweeper:
    def __init__(self):
        self.snapshots = []

    def start_profiling(self):
        tracemalloc.start()

    def take_snapshot(self):
        current, peak = tracemalloc.get_traced_memory()
        snapshot = MemorySnapshot(time.time(), current)
        self.snapshots.append(snapshot)

    def stop_profiling(self):
        tracemalloc.stop()

    def get_memory_usage(self):
        return self.snapshots

def main():
    parser = argparse.ArgumentParser(description='Memory Sweeper')
    parser.add_argument('--interval', type=int, default=1, help='Profiling interval in seconds')
    parser.add_argument('--duration', type=int, default=10, help='Profiling duration in seconds')
    args, unknown = parser.parse_known_args()
    if unknown:
        print("Unrecognized arguments:", unknown)
        return
    sweeper = MemorySweeper()
    sweeper.start_profiling()
    start_time = time.time()
    while time.time() - start_time < args.duration:
        sweeper.take_snapshot()
        time.sleep(args.interval)
    sweeper.stop_profiling()
    memory_usage = sweeper.get_memory_usage()
    print(json.dumps([dataclasses.asdict(snapshot) for snapshot in memory_usage], indent=4))

if __name__ == '__main__':
    main()
