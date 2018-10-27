# Find a free port to use
port=$(echo $((3000 + RANDOM % 7000)))
isfree=$(netstat -tapln | grep $port)

while [[ -n "$isfree" ]]; do
  port=$[port+1]
  isfree=$(netstat -tapln | grep $port)
done

# Configure env files
export PYTHONPATH=$(pwd)
export REDIS_PORT=$port
export REDIS_PASSWORD=$(LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 13 ; echo)

echo "
REDIS_PORT=$REDIS_PORT
REDIS_PASSWORD=$REDIS_PASSWORD
" > docker/redis.env

redis-server docker/redis.conf --port $REDIS_PORT --requirepass $REDIS_PASSWORD 2>/dev/null
