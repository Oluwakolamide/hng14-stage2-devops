#!/bin/bash
set -e

TIMEOUT=120
FRONTEND_URL="http://localhost:3000"

echo "==> Waiting for frontend to be healthy..."
elapsed=0
until curl -sf "$FRONTEND_URL/health" > /dev/null; do
  echo "  Not ready... (${elapsed}s)"
  sleep 5
  elapsed=$((elapsed + 5))
  if [ $elapsed -ge $TIMEOUT ]; then
    echo "Timeout waiting for frontend"
    exit 1
  fi
done
echo "  Frontend healthy."

echo "==> Submitting job..."
JOB_RESP=$(curl -sf -X POST "$FRONTEND_URL/submit")
echo "  Response: $JOB_RESP"
JOB_ID=$(echo "$JOB_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['job_id'])")
echo "  Job ID: $JOB_ID"

echo "==> Polling for completion..."
elapsed=0
while [ $elapsed -lt 60 ]; do
  STATUS=$(curl -sf "$FRONTEND_URL/status/$JOB_ID" | \
    python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
  echo "  Status: $STATUS (${elapsed}s)"
  if [ "$STATUS" = "completed" ]; then
    echo "✅ Job completed successfully."
    exit 0
  fi
  sleep 2
  elapsed=$((elapsed + 2))
done

echo "❌ Job did not complete within 60 seconds."
exit 1
