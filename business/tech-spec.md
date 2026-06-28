```markdown
# Technical Specification: Memory Sweeper v1

## Stack
- **Language**: Python
- **Framework**: FastAPI
- **Runtime**: Python 3.10+
- **Database**: PostgreSQL
- **Vector Database**: pgvector
- **Orchestration**: Docker + Kubernetes
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Tracing**: Jaeger

## Hosting
- **Free-Tier-First**: AWS Free Tier (EC2, RDS, S3)
- **Production**: AWS EKS (Elastic Kubernetes Service)
- **Database**: AWS RDS PostgreSQL
- **Vector Database**: AWS RDS with pgvector extension
- **Storage**: AWS S3 for storing memory profiles and reports

## Data Model
### Tables/Collections
1. **MemoryProfiles**
   - `id`: UUID (Primary Key)
   - `codebase_id`: UUID (Foreign Key)
   - `profile_name`: String
   - `created_at`: Timestamp
   - `updated_at`: Timestamp
   - `status`: String (e.g., "pending", "completed", "failed")

2. **Codebases**
   - `id`: UUID (Primary Key)
   - `name`: String
   - `repository_url`: String
   - `created_at`: Timestamp
   - `updated_at`: Timestamp

3. **MemoryLeaks**
   - `id`: UUID (Primary Key)
   - `profile_id`: UUID (Foreign Key)
   - `location`: String (file path and line number)
   - `description`: String
   - `severity`: String (e.g., "low", "medium", "high")
   - `created_at`: Timestamp

4. **PerformanceBottlenecks**
   - `id`: UUID (Primary Key)
   - `profile_id`: UUID (Foreign Key)
   - `location`: String (file path and line number)
   - `description`: String
   - `severity`: String (e.g., "low", "medium", "high")
   - `created_at`: Timestamp

## API Surface
1. **POST /api/codebases**
   - Purpose: Create a new codebase entry.

2. **GET /api/codebases**
   - Purpose: List all codebases.

3. **GET /api/codebases/{codebase_id}**
   - Purpose: Retrieve details of a specific codebase.

4. **POST /api/memory-profiles**
   - Purpose: Initiate a new memory profiling job.

5. **GET /api/memory-profiles**
   - Purpose: List all memory profiles.

6. **GET /api/memory-profiles/{profile_id}**
   - Purpose: Retrieve details of a specific memory profile.

7. **GET /api/memory-profiles/{profile_id}/leaks**
   - Purpose: List all memory leaks for a specific profile.

8. **GET /api/memory-profiles/{profile_id}/bottlenecks**
   - Purpose: List all performance bottlenecks for a specific profile.

9. **GET /api/memory-profiles/{profile_id}/report**
   - Purpose: Generate and retrieve a report for a specific memory profile.

10. **GET /api/memory-profiles/{profile_id}/status**
    - Purpose: Check the status of a specific memory profile.

## Security Model
- **Authentication**: JWT (JSON Web Tokens)
- **Authorization**: Role-Based Access Control (RBAC)
  - Roles: `admin`, `developer`, `viewer`
  - Permissions:
    - `admin`: Full access to all endpoints.
    - `developer`: Can create and manage codebases and memory profiles.
    - `viewer`: Can view codebases and memory profiles but cannot modify them.
- **Secrets Management**: AWS Secrets Manager
- **IAM**: AWS IAM for managing access to AWS resources.

## Observability
- **Logs**: ELK Stack for centralized logging.
  - Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
  - Log retention: 30 days
- **Metrics**: Prometheus for collecting and storing metrics.
  - Metrics to track:
    - Number of memory profiles created.
    - Number of memory leaks detected.
    - Number of performance bottlenecks detected.
    - API response times.
    - Error rates.
- **Traces**: Jaeger for distributed tracing.
  - Trace context propagation for all API calls.

## Build/CI
- **Version Control**: GitHub
- **CI/CD Pipeline**: GitHub Actions
  - Stages:
    1. **Build**: Build Docker images.
    2. **Test**: Run unit tests and integration tests.
    3. **Deploy**: Deploy to AWS EKS.
  - Triggers:
    - On push to `main` branch.
    - On pull request to `main` branch.
  - Artifacts:
    - Docker images pushed to AWS ECR.
    - Test reports stored as artifacts.
```