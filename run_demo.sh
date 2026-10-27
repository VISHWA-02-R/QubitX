#!/bin/bash
# run_demo.sh -- one-command orchestration for the live demo
# Run this on the DEFENDER laptop after uvicorn is already running.

SERVER="http://127.0.0.1:8000"
SESSION="sess_demo1"

echo "Starting legit bot (baseline traffic)..."
python clients/bot_legit.py --server $SERVER --session $SESSION --rate 1 &
LEGIT_PID=$!

sleep 3
echo "Firing forge bot..."
python clients/bot_forge.py --server $SERVER --session $SESSION --rate 0.5 &
FORGE_PID=$!

sleep 5
echo "Firing replay bot..."
python clients/bot_replay.py --server $SERVER --session $SESSION

sleep 3
echo "Firing impersonation bot..."
python clients/bot_impersonate.py --server $SERVER --session $SESSION --fake-identity bob

echo "Demo sequence complete. Ctrl+C to stop legit/forge bots."
wait $LEGIT_PID $FORGE_PID
