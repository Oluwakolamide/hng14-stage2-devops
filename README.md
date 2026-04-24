# HNG Internship XIV — Stage 2 DevOps: Containerised Job Processing System

A production-ready, containerised multi-service job processing application consisting of a Node.js frontend, a Python/FastAPI backend, a Python worker, and Redis — all wired together with Docker Compose and a full GitHub Actions CI/CD pipeline.

---

## Architecture

```
Browser
  │
  ▼
Frontend (Node.js :3000)
  │  POST /submit → creates job
  │  GET  /status/:id → polls job status
  ▼
API (FastAPI :8000)
  │  Pushes job IDs to Redis list "job"
  │  Reads/writes job status hashes in Redis
  ▼
Redis (:6379, internal only)
  ▲
  │  Pops job IDs with BRPOP
Worker (Python)
  │  Sets job status to "completed"
```

All four services communicate over a named internal Docker network. Redis is never exposed on the host.

---

## Prerequisites

| Tool | Minimum version |
|------|----------------|
| Docker | 24.x |
| Docker Compose (plugin) | 2.x |
| Git | any recent |

No cloud account, no paid service, and no extra tooling is required.

---

## Quick Start (clean machine)

### 1. Clone your fork

```bash
git clone https://github.com/<YOUR_GITHUB_USERNAME>/hng14-stage2-devops.git
cd hng14-stage2-devops
```

### 2. Create your `.env` file

```bash
cp .env.example .env
```

Open `.env` and set a strong Redis password:

```
REDIS_PASSWORD=your_strong_password_here
FRONTEND_PORT=3000
```

### 3. Build and start the stack

```bash
docker compose up -d --build
```

### 4. Verify successful startup

All four services must show `(healthy)` before the application is ready:

```bash
docker compose ps
```

Expected output:

```
NAME                    IMAGE       STATUS
project-redis-1         redis:7-alpine     Up (healthy)
project-api-1           project-api        Up (healthy)
project-worker-1        project-worker     Up (healthy)
project-frontend-1      project-frontend   Up (healthy)
```

If any service shows `(starting)`, wait a few seconds and re-run `docker compose ps`.
If any shows `(unhealthy)`, inspect the logs: `docker compose logs <service-name>`.

### 5. Access the application

Open your browser at: **http://localhost:3000**

Click **Submit New Job**. The job ID will appear and its status will update from `queued` → `completed` within a few seconds.

---

## Verifying the API directly

```bash
# Create a job
curl -X POST http://localhost:8000/jobs
# → {"job_id":"<uuid>"}

# Check job status
curl http://localhost:8000/jobs/<uuid>
# → {"job_id":"<uuid>","status":"completed"}

# Health checks
curl http://localhost:8000/health
curl http://localhost:3000/health
```

---

## Running the test suite locally

```bash
cd api
pip install -r requirements.txt pytest pytest-cov httpx
pytest tests/ --cov=. -v
```

---

## Stopping the stack

```bash
docker compose down          # stop and remove containers
docker compose down -v       # also remove volumes (clears Redis data)
```

---

## CI/CD Pipeline

The GitHub Actions pipeline at `.github/workflows/ci.yml` runs on every push and enforces these stages in strict order:

| Stage | What it does |
|-------|-------------|
| **lint** | flake8 (Python), ESLint (JavaScript), hadolint (all Dockerfiles) |
| **test** | pytest with Redis mocked, uploads coverage XML + HTML as artifact |
| **build** | Builds all three images, tags with git SHA and `latest`, pushes to an in-job local registry |
| **security** | Trivy scans all images, fails pipeline on any CRITICAL CVE, uploads SARIF results |
| **integration-test** | Brings up the full stack, submits a real job, polls until `completed`, tears down |
| **deploy** | SSH rolling update to server — new container must pass healthcheck before old one stops (main branch only) |

A failure at any stage prevents all subsequent stages from running.

### Deploy secrets required

Set these in your GitHub repository → Settings → Secrets and variables → Actions:

| Secret | Description |
|--------|-------------|
| `DEPLOY_HOST` | IP address or hostname of your server |
| `DEPLOY_USER` | SSH user on the server |
| `DEPLOY_SSH_KEY` | Private SSH key with access to the server |

---

## Project structure

```
.
├── .env.example              # Template — copy to .env, never commit .env
├── .gitignore
├── .github/
│   └── workflows/
│       └── ci.yml            # Full CI/CD pipeline
├── docker-compose.yml
├── README.md
├── FIXES.md                  # All bugs found and fixed
├── api/
│   ├── Dockerfile
│   ├── main.py
│   ├── requirements.txt
│   └── tests/
│       ├── __init__.py
│       └── test_main.py
├── worker/
│   ├── Dockerfile
│   ├── worker.py
│   ├── healthcheck.py
│   └── requirements.txt
└── frontend/
    ├── Dockerfile
    ├── app.js
    ├── package.json
    ├── .eslintrc.json
    └── views/
        └── index.html
```
