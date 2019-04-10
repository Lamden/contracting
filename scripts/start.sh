#!/bin/bash
# Configure env files
export PYTHONPATH=$(pwd)

echo "Starting Ledis server..."
#pkill -9 redis-server
#redis-server 2>/dev/null >/dev/null &
pkill -9 ledis-server
ledis-server -addr localhost:6379 &
sleep 1
echo "Done."
