# Memory Sweeper – Cloud Cost Impact Dashboard (Prototype)

This tiny Python library demonstrates the core logic behind the **Memory‑Sweeper** product:

* **Ingest** CSV cost metrics (e.g., AWS EC2 memory‑GB‑hour).
* **Compute** daily memory usage deltas from snapshots.
* **Estimate** incremental cost caused by a memory increase.
* **Generate** a 30‑day time‑series that flags possible leaks.
* **Export** the result as CSV for downstream UI consumption.

The implementation uses only the Python standard library and is fully covered by unit tests.

## Quick start
