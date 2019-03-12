#!/bin/bash
# Configure env files
export PYTHONPATH=$(pwd)

echo "Starting Redis server..."
#pkill -9 redis-server
#redis-server 2>/dev/null >/dev/null &
pkill -9 ledis-server
ledis-server -addr localhost:6379 2>/dev/null >/dev/null &
sleep 1
echo "Done."