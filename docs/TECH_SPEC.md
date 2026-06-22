# TECH_SPEC.md  

**Project:** memory‑sweeper  
**Team:** Axentx – Product Engineering  
**Owner:** Senior Product/Engineering Lead  
**Status:** Draft – ready for review  

---  

## 1. Overview  

**memory‑sweeper** is a static‑and‑dynamic memory profiling platform designed for large‑scale codebases (C/C++, Rust, Go, Java). It scans source trees, builds an abstract memory model, runs instrumented workloads, and produces a ranked list of memory‑leak hotspots, high‑allocation call‑paths, and actionable remediation recommendations.  

Key goals:  

| Goal | Success Metric |
|------|----------------|
| **Accuracy** | ≥ 95 % recall of known leaks in benchmark suites (e.g., LLM‑Bench, SPEC CPU) |
| **Scalability** | Process ≥ 10 M LOC in ≤ 30 min on a 32‑core node |
| **Actionability** | ≥ 80 % of reported items have an auto‑generated fix suggestion |
| **Integrations** | CI/CD plug‑in for GitHub Actions, GitLab CI, Azure Pipelines |
| **Security** | No code execution beyond sandboxed instrumentation; all data stored encrypted at rest |

---  

## 2. Architecture Overview  

```
+-------------------+          +-------------------+          +-------------------+
|   CLI / UI Front  | <--API--> |   Orchestrator    | <--RPC--> |   Workers (Pool) |
+-------------------+          +-------------------+          +-------------------+
          |                               |                               |
          |                               |                               |
          v                               v                               v
+-------------------+          +-------------------+          +-------------------+
|   Repository      |          |   Analyzer Engine |          |   Instrumentation |
|   Scanner (git)   |          |   (static + dyn)  |          |   Runtime Agent   |
+-------------------+          +-------------------+          +-------------------+
          |                               |                               |
          +-------------------+-----------+-----------+-------------------+
                              |                       |
                              v                       v
                     +-------------------+   +-------------------+
                     |   Data Store      |   |   Recommendation  |
                     |   (PostgreSQL)    |   |   Engine (LLM)    |
                     +-------------------+   +-------------------+
```

* **CLI / UI Front** – `memory-sweeper` binary (CLI) and optional React web UI for interactive reports.  
* **Orchestrator** – Central process (Python 3.11) that receives jobs, schedules workers, aggregates results, and persists to the DB.  
* **Workers** – Containerised pods (Docker) that run static analysis (Clang‑Tooling, Rust‑Analyzer) and dynamic instrumentation (eBPF‑based probes, JVMTI, Go pprof).  
* **Repository Scanner** – Clones the target repo, extracts build graph via `bazel`/`cmake`/`cargo`/`maven`.  
* **Analyzer Engine** – Combines static call‑graph, allocation sites, and runtime heap snapshots into a unified **Memory Graph**.  
* **Instrumentation Runtime** – Light‑weight agents injected at build time; they stream allocation events to a local collector (gRPC).  
* **Data Store** – PostgreSQL 15 with TimescaleDB extension for time‑series heap‑snapshot storage.  
* **Recommendation Engine** – Uses an LLM (vLLM backend) fine‑tuned on 10 k curated memory‑leak fixes to generate “fix snippets” and priority scores.  

---  

## 3. Core Components  

| Component | Language / Runtime | Description | Key Interfaces |
|-----------|--------------------|-------------|----------------|
| **CLI** | Rust (binary) | Parses args, launches orchestrator via gRPC, formats final report (JSON/HTML). | `memory-sweeper run <options>` |
| **Web UI** | React + TypeScript | Dashboard for historical runs, diff view, drill‑down on call‑paths. | REST `/api/v1/*` |
| **Orchestrator** | Python 3.11 (FastAPI) | Job queue (Redis), worker dispatcher, result aggregator. | gRPC `WorkerService`, HTTP `/jobs` |
| **Worker** | Python + C++ extensions | Executes static analysis (Clang‑Tooling), dynamic probes (eBPF), merges results. | gRPC `AnalyzeRequest/Response` |
| **Static Analyzer** | C++ (Clang‑LibTooling) | Generates allocation site map, lifetimes, potential dangling pointers. | Input: source tree, compile_commands.json |
| **Dynamic Instrumentation** | C (eBPF), Java (JVMTI), Go (runtime/pprof) | Captures live allocation/free events, heap snapshots. | Stream to local collector (gRPC) |
| **Data Store** | PostgreSQL 15 + TimescaleDB | Stores run metadata, memory graphs, snapshots, recommendations. | SQL + JSONB columns |
| **Recommendation Engine** | Python (vLLM) | LLM inference service (GPU‑accelerated) that produces fix suggestions. | HTTP `/v1/completions` |
| **CI/CD Plug‑ins** | YAML templates | GitHub Action, GitLab CI, Azure Pipelines wrappers. | Calls CLI in `--ci` mode |

---  

## 4. Data Model  

### 4.1 Primary Tables (PostgreSQL)

| Table | Columns | Description |
|-------|---------|-------------|
| `runs` | `id PK`, `repo_url`, `commit_sha`, `started_at`, `finished_at`, `status`, `config JSONB` | One analysis execution. |
| `allocation_sites` | `id PK`, `run_id FK`, `file_path`, `line`, `function`, `size_bytes`, `allocation_type`, `static_score` | Static allocation metadata. |
| `heap_snapshots` | `id PK`, `run_id FK`, `timestamp`, `snapshot JSONB` | Serialized memory graph at a point in time. |
| `leak_candidates` | `id PK`, `run_id FK`, `site_id FK`, `severity`, `confidence`, `recommendation_id FK` | Ranked leak findings. |
| `recommendations` | `id PK`, `candidate_id FK`, `prompt`, `response`, `model_version`, `generated_at` | LLM‑generated fix snippet. |
| `ci_reports` | `id PK`, `run_id FK`, `status`, `markdown_report` | Rendered report for CI pipelines. |

### 4.2 Memory Graph (JSONB schema)

```json
{
  "nodes": [
    {"id":"alloc_123","type":"allocation","size":4096,"location":"src/foo.c:42"},
    {"id":"obj_456","type":"object","class":"std::vector","size":128}
  ],
  "edges": [
    {"src":"alloc_123","dst":"obj_456","type":"owns"},
    {"src":"obj_456","dst":"alloc_789","type":"references"}
  ],
  "metadata": {"timestamp":"2026-06-22T14:33:00Z"}
}
```

---  

## 5. Key APIs / Interfaces  

### 5.1 gRPC (Orchestrator ↔ Workers)

```proto
service WorkerService {
  rpc Analyze (AnalyzeRequest) returns (AnalyzeResponse);
}

message AnalyzeRequest {
  string run_id = 1;
  string repo_path = 2;
  repeated string targets = 3; // e.g., ["src/", "tests/"]
  map<string, string> build_env = 4;
  bool enable_dynamic = 5;
}

message AnalyzeResponse {
  string run_id = 1;
  repeated AllocationSite static_sites = 2;
  repeated HeapSnapshot snapshots = 3;
  repeated LeakCandidate candidates = 4;
}
```

### 5.2 REST (Web UI ↔ Orchestrator)

| Method | Path | Description |
|--------|------|-------------|
| `GET /api/v1/runs` | List recent runs |
| `GET /api/v1/runs/{id}` | Run details + summary |
| `GET /api/v1/runs/{id}/report` | Rendered HTML/JSON report |
| `POST /api/v1/runs` | Submit new analysis (payload = repo URL, commit, config) |

### 5.3 CLI Flags  

| Flag | Description |
|------|-------------|
| `--repo <url>` | Git URL (HTTPS or SSH). |
| `--commit <sha>` | Specific commit to analyze. |
| `--targets <paths>` | Relative paths to include. |
| `--static-only` | Skip dynamic instrumentation. |
| `--ci` | Produce CI‑compatible markdown output. |
| `--output <dir>` | Directory for generated artifacts. |

---  

## 6. Technology Stack  

| Layer | Choice | Rationale |
|-------|--------|-----------|
| **Language (core)** | Rust (CLI) + Python 3.11 (Orchestrator) | Rust gives fast, safe binary; Python enables rapid ML integration. |
| **Static Analysis** | Clang‑LibTooling (C/C++), Rust‑Analyzer, Spoon (Java) | Proven, open‑source parsers with AST support. |
| **Dynamic Instrumentation** | eBPF (bcc), JVMTI, Go runtime/pprof | Low overhead, kernel‑level visibility, language‑specific hooks. |
| **LLM Inference** | vLLM (GPU‑accelerated) | Scalable, supports quantized models; already vetted in AXENTX playbook. |
| **Container Runtime** | Docker + Kubernetes (Helm chart) | Horizontal scaling of workers. |
| **Message Queue** | Redis Streams | Simple, low‑latency job dispatch. |
| **Database** | PostgreSQL 15 + TimescaleDB | Strong relational model + time‑series for snapshots. |
| **Web UI** | React 18 + Vite, TypeScript | Fast dev cycle, easy bundling. |
| **CI Integration** | YAML templates (GitHub Actions, GitLab CI) | Minimal friction for customers. |

---  

## 7. Dependencies  

| Dependency | Version | License |
|------------|---------|---------|
| `clang` | 18.1.0 | Apache‑2.0 |
| `rustc` | 1.78.0 | MIT/Apache‑2.0 |
| `vllm` | 0.5.0 | Apache‑2.0 |
| `redis` | 7.2 | BSD‑3 |
| `postgresql` | 15 | PostgreSQL |
| `timescaledb` | 2.12 | Apache‑2.0 |
| `react` | 18.2.0 | MIT |
| `eBPF/bcc` | 0.31.0 | Apache‑2.0 |
| `jvmti` | JDK 21 | GPL‑2 with Classpath Exception |
| `go` | 1.22 | BSD‑3 |

All third‑party libraries are vetted for commercial use per AXENTX compliance checklist.

---  

## 8. Deployment Diagram  

```
+-------------------+      +-------------------+      +-------------------+
|   GitHub Actions  | ---> |  API Gateway (NGINX) | --> |  Orchestrator (Python) |
+-------------------+      +-------------------+      +-------------------+
                                   |                     |
                                   v                     v
                         +-------------------+   +-------------------+
                         |   Redis (Streams) |   |   PostgreSQL + TS |
                         +-------------------+   +-------------------+
                                   |                     |
                                   v                     v
                         +-------------------+   +-------------------+
                         |   Worker Pods (K8s)  <--|  vLLM Service   |
                         +-------------------+   +-------------------+
                                   |
                                   v
                         +-------------------+
                         |   Artifact Store (S3) |
                         +-------------------+
```

* **Ingress** – NGINX with TLS termination, JWT auth for internal services.  
* **Scaling** – Horizontal Pod Autoscaler (CPU > 70 % → add worker).  
* **Observability** – Prometheus + Grafana dashboards for job latency, worker health.  
* **Security** – All inter‑service traffic mTLS; data at rest encrypted with AWS KMS.  

---  

## 9. Implementation Milestones  

| Milestone | Scope | Owner | ETA |
|-----------|-------|-------|-----|
| **M1 – Core CLI & Orchestrator** | Repo cloning, static analysis pipeline, JSON report | Lead Engineer (Rust) / Backend Engineer (Python) | 4 weeks |
| **M2 – Dynamic Instrumentation** | eBPF collector, JVM/Go agents, snapshot storage | Systems Engineer | 3 weeks |
| **M3 – Data Store & API** | PostgreSQL schema, FastAPI endpoints, Redis queue | DB Engineer | 2 weeks |
| **M4 – Recommendation Engine** | Fine‑tune LLM on leak‑fix corpus, integrate vLLM | ML Engineer | 3 weeks |
| **M5 – CI/CD Plug‑ins** | GitHub Action, GitLab CI templates, markdown report | DevOps Engineer | 1 week |
| **M6 – Web UI MVP** | Dashboard, run list, detailed leak view | Front‑end Engineer | 4 weeks |
| **M7 – Production Hardening** | Autoscaling, observability, security audit | Site Reliability Engineer | 2 weeks |
| **M8 – Beta Release & Feedback Loop** | Pilot with 3 external customers, collect WTP data | PM / Customer Success | 2 weeks |

Total estimated delivery: **~20 weeks** (5 months).  

---  

## 10. Risks & Mitigations  

| Risk | Impact | Mitigation |
|------|--------|------------|
| **False positives** in static analysis | Customer distrust | Calibrate thresholds; expose confidence scores; allow suppression rules. |
| **Instrumentation overhead** > 10 % | CI time blow‑out | Use eBPF sampling mode; allow `--light` flag for CI runs. |
| **LLM hallucination** in recommendations | Bad code changes | Post‑process with static verifier; require human approval before applying. |
| **Large repo cloning** exceeds storage | Cost & latency | Support shallow clone + incremental analysis; cache layers in S3. |
| **Security of injected agents** | Potential attack surface | Run agents in isolated namespaces; sign binaries; audit code paths. |

---  

## 11. Glossary  

- **Static Analysis** – Compile‑time inspection of source code without execution.  
- **Dynamic Instrumentation** – Runtime collection of memory events via probes.  
- **Leak Candidate** – Allocation site with high confidence of being unreleased.  
- **Recommendation Engine** – LLM service that produces fix snippets.  
- **CI Mode** – Reduced‑overhead run that outputs a markdown summary for pipelines.  

---  

*Prepared by the memory‑sweeper engineering team. Review and sign‑off required before moving to implementation.*
