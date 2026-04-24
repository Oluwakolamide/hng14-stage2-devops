# FIXES.md — Bug Report for HNG Stage 2 Starter Application

Every issue found in the original source, with file, line, description, and fix applied.

---

## FIX-01: Real credentials committed to version control

**File:** `api/.env`
**Line:** 1–2
**Problem:** The `.env` file containing `REDIS_PASSWORD=supersecretpassword123` was committed to git. Any secret committed to a repository is permanently exposed in git history even after deletion. There was also no `.gitignore` in the repository, which is the direct cause.
**Fix:** Deleted `api/.env`. Added a root-level `.gitignore` with rules for `.env`, `*.env`, and common Python/Node build artifacts. Added `.env.example` with placeholder values so developers know which variables are required without exposing real credentials.

---

## FIX-02: Redis host hardcoded to `localhost` in API

**File:** `api/main.py`
**Line:** 8
**Problem:** `r = redis.Redis(host="localhost", port=6379)` — inside Docker, each service runs in its own container. The API cannot reach Redis via `localhost`; it must use the Redis container's service name on the shared Docker network.
**Fix:** Changed to `host=os.environ.get("REDIS_HOST", "redis")` so the host is configurable via environment variable, defaulting to `"redis"` (the Compose service name).

---

## FIX-03: Redis password not used in API connection

**File:** `api/main.py`
**Line:** 8
**Problem:** The `.env` set `REDIS_PASSWORD` but the Redis client was instantiated without a `password` argument. Any Redis instance started with `--requirepass` would reject every connection with an `AUTHFAIL` error.
**Fix:** Added `password=os.environ.get("REDIS_PASSWORD") or None` to the `redis.Redis()` call.

---

## FIX-04: `os` module imported but never used for configuration

**File:** `api/main.py`
**Line:** 4
**Problem:** `import os` was present but `os` was never referenced. With the original code the import was dead weight; without it the env-var reads in fixes 02/03 would fail.
**Fix:** `os` is now actively used for `os.environ.get(...)` calls for `REDIS_HOST`, `REDIS_PORT`, and `REDIS_PASSWORD`.

---

## FIX-05: `get_job` returns HTTP 200 for jobs that do not exist

**File:** `api/main.py`
**Line:** 20–22
**Problem:** When a job ID is not found, the endpoint returned `{"error": "not found"}` with a `200 OK` status code. Callers — including the integration test — cannot reliably distinguish between a found and not-found job without inspecting the response body.
**Fix:** Replaced the `return {"error": "not found"}` with `raise HTTPException(status_code=404, detail="Job not found")` so the response correctly uses HTTP 404.

---

## FIX-06: `status.decode()` on a potentially undecodable value

**File:** `api/main.py`
**Line:** 21
**Problem:** The original code called `status.decode()` on the result of `r.hget()`. If Redis were ever configured with `decode_responses=True`, this would raise `AttributeError: 'str' object has no attribute 'decode'`. Additionally, relying on manual `.decode()` throughout the codebase is fragile.
**Fix:** Enabled `decode_responses=True` on the Redis client so all values are returned as native Python strings. Removed all `.decode()` calls.

---

## FIX-07: No `/health` endpoint in the API

**File:** `api/main.py`
**Line:** — (missing)
**Problem:** Docker `HEALTHCHECK` instructions and `depends_on: condition: service_healthy` in Compose both require a reliable endpoint to probe. Without one, a Dockerfile `HEALTHCHECK` must resort to fragile process-level checks and Compose cannot gate dependent services.
**Fix:** Added `GET /health` returning `{"status": "ok"}` with HTTP 200.

---

## FIX-08: No version pins in API requirements

**File:** `api/requirements.txt`
**Lines:** 1–3
**Problem:** `fastapi`, `uvicorn`, and `redis` were listed without version specifiers. This produces non-deterministic builds — a package update on PyPI can silently break the application between CI runs or deployments.
**Fix:** Pinned all packages: `fastapi==0.110.0`, `uvicorn[standard]==0.29.0`, `redis==5.0.3`.

---

## FIX-09: Redis host hardcoded to `localhost` in worker

**File:** `worker/worker.py`
**Line:** 6
**Problem:** Same container networking issue as FIX-02. The worker cannot reach Redis via `localhost` inside Docker.
**Fix:** Changed to `host=os.environ.get("REDIS_HOST", "redis")`.

---

## FIX-10: Redis password not used in worker connection

**File:** `worker/worker.py`
**Line:** 6
**Problem:** Same as FIX-03. Worker connections would be rejected by a password-protected Redis.
**Fix:** Added `password=os.environ.get("REDIS_PASSWORD") or None` to the worker's `redis.Redis()` call.

---

## FIX-11: `signal` imported but SIGTERM/SIGINT handlers never registered

**File:** `worker/worker.py`
**Line:** 4
**Problem:** `import signal` was present but no handlers were registered. When Docker stops a container it sends `SIGTERM`, and if unhandled the process receives `SIGKILL` after the grace period with no clean shutdown. Jobs in-flight could be silently lost.
**Fix:** Registered handlers for both `SIGTERM` and `SIGINT` that set a `running` flag to `False`. The main loop checks `while running:` so the worker finishes any current job before exiting and logs a clean shutdown message.

---

## FIX-12: No version pin in worker requirements

**File:** `worker/requirements.txt`
**Line:** 1
**Problem:** `redis` listed with no version specifier — same non-determinism issue as FIX-08.
**Fix:** Pinned to `redis==5.0.3` to match the API service.

---

## FIX-13: API URL hardcoded to `localhost` in frontend

**File:** `frontend/app.js`
**Line:** 6
**Problem:** `const API_URL = "http://localhost:8000"` — inside Docker the frontend container cannot reach the API container via localhost. Calls to `/submit` and `/status/:id` would all fail with connection refused.
**Fix:** Changed to `const API_URL = process.env.API_URL || 'http://api:8000'` so the URL is injected via environment variable (set to `http://api:8000` in Compose).

---

## FIX-14: Frontend port hardcoded, not configurable

**File:** `frontend/app.js`
**Line:** 35 (original)
**Problem:** `app.listen(3000, ...)` hardcodes the port, making it impossible to change without modifying source code.
**Fix:** Changed to `app.listen(process.env.PORT || 3000, ...)`.

---

## FIX-15: No `/health` endpoint in the frontend

**File:** `frontend/app.js`
**Line:** — (missing)
**Problem:** Same issue as FIX-07. Without a health endpoint, the frontend Dockerfile cannot have a useful `HEALTHCHECK` and Compose cannot make `depends_on: condition: service_healthy` work for any service that depends on the frontend.
**Fix:** Added `GET /health` returning `{"status": "ok"}`.

---

## FIX-16: No `.gitignore` in repository

**File:** `.gitignore` (missing)
**Line:** — (missing entirely)
**Problem:** The absence of a `.gitignore` is the root cause of FIX-01 — the `.env` file was never excluded from tracking. It would also allow `node_modules/`, `__pycache__/`, `.coverage`, and other generated files to be committed accidentally.
**Fix:** Added a comprehensive `.gitignore` at the repository root covering `.env`, Python build artifacts, Node modules, IDE files, and Docker image tarballs.
