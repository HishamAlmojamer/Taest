#!/bin/sh
set -eu

cd /app/backend
/opt/venv/bin/alembic upgrade head

# The backend emits ledger events to the gateway. In the combined container the
# public port is assigned by the platform (Render sets PORT), so derive it here.
export GATEWAY_URL="${GATEWAY_URL:-http://127.0.0.1:${PORT:-3001}}"

/opt/venv/bin/uvicorn app.main:app \
    --host 127.0.0.1 \
    --port 8001 \
    --proxy-headers \
    --forwarded-allow-ips='*' &
BACKEND_PID=$!

NODE_PID=""
cleanup() {
    [ -n "$NODE_PID" ] && kill -TERM "$NODE_PID" 2>/dev/null || true
    kill -TERM "$BACKEND_PID" 2>/dev/null || true
}
trap cleanup TERM INT

# Give the backend time to finish startup migrations before accepting traffic.
i=0
while [ "$i" -lt 90 ]; do
    if /opt/venv/bin/python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8001/api/health', timeout=2)" 2>/dev/null; then
        break
    fi
    i=$((i + 1))
    sleep 1
done

cd /app/gateway
node dist/index.js &
NODE_PID=$!

wait "$NODE_PID"
