import redis
import time
import os
import signal
import sys

running = True


def handle_shutdown(signum, frame):
    global running
    print("Shutdown signal received, stopping worker...", flush=True)
    running = False


signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

r = redis.Redis(
    host=os.environ.get("REDIS_HOST", "redis"),
    port=int(os.environ.get("REDIS_PORT", 6379)),
    password=os.environ.get("REDIS_PASSWORD") or None,
    decode_responses=True,
)


def process_job(job_id):
    print(f"Processing job {job_id}", flush=True)
    time.sleep(2)  # simulate work
    r.hset(f"job:{job_id}", "status", "completed")
    print(f"Done: {job_id}", flush=True)


while running:
    job = r.brpop("job", timeout=5)
    if job:
        _, job_id = job
        process_job(job_id)

print("Worker exited cleanly.", flush=True)
sys.exit(0)
