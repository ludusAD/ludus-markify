#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

# Use the project's virtual environment when it exists and none is active.
if [ -z "$VIRTUAL_ENV" ] && [ -f .venv/bin/activate ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

if ! command -v uvicorn >/dev/null 2>&1; then
  echo "uvicorn not found. Create the virtual environment first:"
  echo "  python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

# Refuse to start if a port is taken. Never kill processes we did not start.
port_in_use() { (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null; }
for PORT in 8000 3333; do
  if port_in_use "$PORT"; then
    echo "Port $PORT is already in use. Stop whatever uses it, then run ./start.sh again."
    echo "See what uses it: ss -ltnp | grep :$PORT"
    exit 1
  fi
done

# Start backend
uvicorn backend.server:app --reload --port 8000 &
BACKEND_PID=$!
echo "Backend started (PID $BACKEND_PID)"

# Start frontend
(cd frontend && exec npm run dev) &
FRONTEND_PID=$!
echo "Frontend started (PID $FRONTEND_PID)"

echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3333"
echo ""
echo "Press Ctrl+C to stop both."

# On Ctrl+C, stop only the two processes started above
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM

wait
