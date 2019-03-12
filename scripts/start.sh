# Configure env files
export PYTHONPATH=$(pwd)

echo "Starting Redis server..."
pkill -9 ledis-server
ledis-server -p 6379 2>/dev/null >/dev/null &
sleep 1
echo "Done."