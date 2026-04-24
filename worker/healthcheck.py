import redis
import os
import sys

try:
    r = redis.Redis(
        host=os.environ.get("REDIS_HOST", "redis"),
        port=int(os.environ.get("REDIS_PORT", 6379)),
        password=os.environ.get("REDIS_PASSWORD") or None,
    )
    r.ping()
    sys.exit(0)
except Exception as e:
    print(f"Health check failed: {e}", file=sys.stderr)
    sys.exit(1)
