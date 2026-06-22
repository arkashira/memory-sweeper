# REQUIREMENTS.md

## 1. Overview
**Product:** *memory‑sweeper*  
**Purpose:** Provide developers of large‑scale codebases with automated memory‑profiling, leak detection, and actionable optimization recommendations. The tool must integrate with existing CI pipelines, support multiple languages, and present results in both CLI and web UI formats.

---

## 2. Functional Requirements

| ID | Description |
|----|-------------|
| **FR‑1** | **Language Support** – The tool shall analyze source code written in **C/C++**, **Rust**, **Java**, and **Python**. New language modules must be pluggable via a defined SDK. |
| **FR‑2** | **Static Analysis** – Parse the entire codebase to build an abstract syntax tree (AST) and identify allocation sites, reference lifetimes, and potential dangling pointers. |
| **FR‑3** | **Dynamic Profiling** – When executed against a running binary (or interpreter), collect heap allocation/deallocation events with timestamps and call‑stack traces. |
| **FR‑4** | **Leak Detection** – Flag any allocation that is not freed within a configurable time‑window (default 30 s) or that survives program termination. |
| **FR‑5** | **Bottleneck Identification** – Compute per‑function and per‑module memory‑usage statistics (peak, average, growth rate) and highlight the top 10 contributors to memory pressure. |
| **FR‑6** | **Recommendation Engine** – For each flagged issue, generate a concrete suggestion (e.g., “use `std::unique_ptr`”, “replace `list` with `vector`”, “add explicit `close()`”). |
| **FR‑7** | **CLI Interface** – Provide commands: `scan`, `profile`, `report`, `export`. Output must be machine‑readable JSON and human‑readable colored text. |
| **FR‑8** | **Web UI Dashboard** – Visualize results: heat‑maps of memory usage over time, call‑graph overlays, and drill‑down tables. Must be served via a lightweight HTTP server bundled with the binary. |
| **FR‑9** | **CI/CD Integration** – Export results as JUnit‑compatible XML and GitHub‑compatible annotations so that pipelines can fail on “critical” leaks. |
| **FR‑10** | **Baseline Comparison** – Store previous scan profiles and allow diffing to detect regressions or improvements. |
| **FR‑11** | **Export Formats** – Allow exporting reports in JSON, CSV, and Markdown. |
| **FR‑12** | **Configuration** – All thresholds (leak time‑window, severity levels, ignored paths) must be configurable via a single `memory-sweeper.yaml` file and overridable via CLI flags. |
| **FR‑13** | **Plugin SDK** – Expose a Rust‑based SDK for third‑party plugins to add custom analysis passes or language front‑ends. |
| **FR‑14** | **Telemetry (opt‑in)** – Collect anonymized usage metrics (tool version, language, number of issues) for product improvement, respecting user privacy. |

---

## 3. Non‑Functional Requirements

| ID | Category | Requirement |
|----|----------|-------------|
| **NFR‑1** | **Performance** | Static analysis of a 1 M line C++ codebase must complete ≤ 120 seconds on a 12‑core CPU (2 GHz). Dynamic profiling overhead must not exceed **5 %** of runtime CPU usage. |
| **NFR‑2** | **Scalability** | The tool shall handle codebases up to **10 GB** of source files and binaries without exceeding 8 GB RAM. |
| **NFR‑3** | **Reliability** | Crash‑free operation: < 0.1 % failure rate across 10 k automated runs. All failures must be logged with reproducible stack traces. |
| **NFR‑4** | **Security** | - No external network calls except optional telemetry (opt‑in). <br> - All file reads are confined to paths explicitly listed in the config. <br> - Output sanitization to prevent HTML/JS injection in the web UI. |
| **NFR‑5** | **Portability** | Binaries must run on Linux (glibc 2.31+), macOS (12+), and Windows (10+). Build scripts must support x86_64 and ARM64. |
| **NFR‑6** | **Usability** | - CLI must provide `--help` with examples. <br> - Web UI must be responsive (≤ 200 ms interaction latency) on a typical laptop browser. |
| **NFR‑7** | **Maintainability** | Code coverage ≥ 85 % (unit + integration). All public APIs documented with Rustdoc/Swagger where applicable. |
| **NFR‑8** | **Compliance** | All third‑party libraries must be compatible with Apache‑2.0, MIT, or BSD licenses. No GPL dependencies. |
| **NFR‑9** | **Observability** | Emit structured logs (JSON) with log levels (debug, info, warn, error). Provide a `--log-format` flag to switch to plain text. |
| **NFR‑10** | **Extensibility** | Plugin SDK versioned with semantic versioning; backward‑compatible minor releases must not break existing plugins. |

---

## 4. Constraints

1. **Technology Stack** – Core engine must be written in **Rust 1.72+** for safety and performance. Language front‑ends may use existing parsers (e.g., `tree-sitter`, `clang‑lib`).  
2. **Data Privacy** – No source code may be transmitted off‑machine unless the user explicitly enables telemetry.  
3. **Release Cadence** – Must align with Axentx quarterly release schedule; first MVP due **2026‑09‑30**.  
4. **Resource Limits** – CI runners provide a maximum of 4 CPU cores and 8 GB RAM; the tool must auto‑scale analysis depth based on available resources.  
5. **Dependency Management** – All dependencies must be vendored or fetched via Cargo with lockfiles committed to the repo.  

---

## 5. Assumptions

| ID | Assumption |
|----|------------|
| **A‑1** | Users have build artifacts (e.g., compiled binaries or `.pyc` files) available for dynamic profiling. |
| **A‑2** | The target codebases compile with debug symbols (`-g`) to enable accurate stack traces. |
| **A‑3** | Teams will integrate the CLI into CI pipelines using standard environment variables (`CI`, `GITHUB_WORKSPACE`). |
| **A‑4** | The underlying OS provides `perf`/`eBPF` (Linux) or equivalent tracing APIs for low‑overhead profiling. |
| **A‑5** | Users have permission to read all source files and binaries within the specified project directory. |
| **A‑6** | The optional telemetry endpoint is hosted by Axentx and complies with GDPR/CCPA. |

---

## 6. Acceptance Criteria (Summary)

- All **FR‑1 – FR‑14** are implemented and demonstrable in a live demo.  
- Performance benchmarks meet **NFR‑1** and **NFR‑2** on the reference dataset (1 M LOC C++ project).  
- No security findings in an internal OWASP‑ZAP scan (covers **NFR‑4**).  
- CI integration test suite passes on Linux, macOS, and Windows runners.  
- Documentation (README, user guide, SDK docs) is complete and versioned.  

--- 

*Prepared by: Senior Product/Engineering Lead, Axentx*  
*Date: 2026‑06‑22*
