# STORIES.md – memory‑sweeper

## Overview
**Product:** memory‑sweeper – a static‑and‑dynamic memory profiling & optimization tool for large codebases.  
**Goal:** Enable engineering teams to detect, understand, and fix memory‑related defects before they reach production, reducing OOM crashes and latency spikes.  

The backlog is organized into **Epics** that map to the MVP (core profiling engine, CI integration, UI dashboard, and actionable recommendations) and subsequent stretch goals (team collaboration, language extensions, enterprise reporting).

---

## EPIC 1 – Core Profiling Engine (MVP)

| # | User Story | Acceptance Criteria |
|---|------------|----------------------|
| 1 | **As a developer, I want to run a memory‑sweep on my repository, so that I get a complete report of all allocations and de‑allocations.** | - CLI command `memsweep scan <path>` accepts a project root.<br>- Scans both compiled binaries (via DWARF symbols) and source files (AST analysis).<br>- Generates a JSON report with total allocated bytes, per‑function allocation counts, and peak memory usage.<br>- Execution time ≤ 2 × project build time for a 1 MLOC codebase. |
| 2 | **As a developer, I want the tool to detect obvious memory leaks, so that I can fix them quickly.** | - Leak detection flags any allocation without a matching free/delete in the same call‑graph path.<br>- Each leak entry includes source file, line, and a stack trace of the allocation path.<br>- False‑positive rate ≤ 5 % on the provided benchmark suite. |
| 3 | **As a DevOps engineer, I want the profiler to run in a CI pipeline, so that regressions are caught automatically.** | - Provides a Docker image `axentx/memory-sweeper:latest` with entrypoint `memsweep ci`.<br>- Returns exit code 0 on “no new leaks” and non‑zero on new/critical leaks.<br>- Emits a SARIF file for import into GitHub/GitLab code‑scanning UI. |
| 4 | **As a developer, I want the report to be visualizable in a web UI, so that I can explore hotspots interactively.** | - A lightweight React dashboard (`memsweep-ui`) reads the JSON report.<br>- Shows a treemap of allocation hotspots by module.<br>- Clicking a node displays source snippets and call‑graph. |
| 5 | **As a QA engineer, I want the tool to run on Linux, macOS, and Windows, so that it works across our build matrix.** | - CI runs on Ubuntu‑22.04, macOS‑13, and Windows‑2022 containers.<br>- All platform‑specific dependencies (e.g., `libdw`, `lldb`) are bundled or documented.<br>- Same JSON schema is produced on all OSes. |

---

## EPIC 2 – Actionable Recommendations (MVP)

| # | User Story | Acceptance Criteria |
|---|------------|----------------------|
| 6 | **As a developer, I want the tool to suggest concrete code changes for each leak, so that I can apply fixes with minimal effort.** | - For each leak, the report includes a “Suggested Fix” field (e.g., “Add `free(ptr);` after line 42”).<br>- Suggestions are generated from a rule‑based engine covering the top 10 leak patterns (missing `free`, mismatched `new/delete`, unclosed `malloc`). |
| 7 | **As a team lead, I want a summary of the top‑5 memory‑heavy modules, so that we can prioritize refactoring.** | - Dashboard includes a “Top Modules” panel sorted by total allocated bytes.<br>- Exportable CSV with module name, allocated bytes, and % of total. |
| 8 | **As a security auditor, I want the tool to flag allocations that could lead to DoS attacks, so that we can harden the product.** | - Detects unbounded allocations (e.g., `malloc(size)` where `size` is user‑controlled without caps).<br>- Flags them with severity “Critical” and links to OWASP CWE‑400. |

---

## EPIC 3 – Team Collaboration & Governance (Stretch)

| # | User Story | Acceptance Criteria |
|---|------------|----------------------|
| 9 | **As a developer, I want to comment on a leak directly in the UI, so that I can discuss it with the team.** | - UI supports inline comments attached to a leak entry.<br>- Comments are stored in a lightweight SQLite DB and exported as Markdown. |
| 10 | **As a release manager, I want to enforce a “no new leaks” gate in PRs, so that we maintain memory quality over time.** | - GitHub Action `memory-sweeper/ci-gate` fails the PR if the SARIF report contains any new “High” severity findings compared to the baseline. |
| 11 | **As an architect, I want to compare memory profiles between two builds, so that I can see the impact of architectural changes.** | - CLI `memsweep compare <report‑old> <report‑new>` produces a diff view highlighting added/removed leaks and allocation delta per module. |
| 12 | **As a compliance officer, I need an audit trail of all scans and fixes, so that we can prove due diligence.** | - Each scan logs a signed SHA‑256 hash of the input binary, the report version, and the user who triggered it.<br>- All logs are append‑only in an immutable S3 bucket. |

---

## EPIC 4 – Language & Platform Extensions (Future)

| # | User Story | Acceptance Criteria |
|---|------------|----------------------|
| 13 | **As a Rust developer, I want native support for `Box`, `Arc`, and `Rc`, so that memory issues in Rust code are covered.** | - Analyzer parses Rust MIR to track heap allocations.<br>- Reports leaks such as cycles with `Rc` without `Weak`. |
| 14 | **As a Java engineer, I want to detect excessive heap usage caused by unbounded collections, so that we can tune GC.** | - Bytecode instrumentation identifies `ArrayList` growth without size caps.<br>- Provides GC‑friendly recommendations (e.g., pre‑size collections). |
| 15 | **As a mobile developer, I want the tool to run on Android and iOS CI runners, so that native apps are also profiled.** | - Provides `memsweep-android` and `memsweep-ios` wrappers that invoke platform‑specific profilers (e.g., `perf`, `Instruments`). |

---

## Prioritization & MVP Scope
1. **Core Profiling Engine** (Stories 1‑5) – foundational capability.  
2. **Actionable Recommendations** (Stories 6‑8) – adds immediate developer value.  
3. **Collaboration & Governance** (Stories 9‑12) – optional for first release but high ROI for larger teams.  
4. **Language & Platform Extensions** (Stories 13‑15) – slated for Q3‑Q4 after MVP validation.

All MVP stories are **shippable** within a single sprint cycle (2 weeks) given the existing codebase (vLLM inference engine, SGLang generation pipeline) and the available datasets for training leak‑detection heuristics.
