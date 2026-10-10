#!/bin/bash
echo "========================================================================="
echo "      TIGERTRACE AI - PENCH TIGER RESERVE FIELD COMMAND CENTER"
echo "              100% Offline Edge Biometric Intelligence"
echo "========================================================================="

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR/TigerTrace_AI"

echo "[1/2] Starting Local Server on http://127.0.0.1:8000..."
python3 ui/app.py &
SERVER_PID=$!

sleep 2

echo "[2/2] Opening Command Center in Browser..."
if which xdg-open > /dev/null; then
  xdg-open http://127.0.0.1:8000
elif which open > /dev/null; then
  open http://127.0.0.1:8000
fi

echo "TigerTrace AI is active! Press [Ctrl+C] to stop."
wait $SERVER_PID
