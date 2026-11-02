#!/usr/bin/env bash
set -e

# Free ports used by backend (8000) and frontend (3333)
for PORT in 8000 3333; do
  PIDS=$(lsof -ti tcp:$PORT 2>/dev/null || true)
  if [ -n "$PIDS" ]; then
    echo "Killing processes on port $PORT: $PIDS"
    kill -9 $PIDS
  fi
done

cd "$(dirname "$0")"

# Start backend
uvicorn backend.server:app --reload --port 8000 &
BACKEND_PID=$!
echo "Backend started (PID $BACKEND_PID)"

# Start frontend
cd frontend
npm run dev &
FRONTEND_PID=$!
echo "Frontend started (PID $FRONTEND_PID)"

echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3333"
echo ""
echo "Press Ctrl+C to stop both."

# On Ctrl+C, kill both
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM

wait
