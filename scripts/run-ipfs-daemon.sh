#!/usr/bin/env bash
set -euo pipefail

API_PORT=${IPFS_API_PORT:-5201}
GATEWAY_PORT=${IPFS_GATEWAY_PORT:-8082}

# 1) If a local ipfs daemon is already running, reuse
if pgrep -x ipfs >/dev/null 2>&1; then
  echo "ipfs daemon appears running; reusing instance" >&2
  exit 0
fi

# 2) If ipfs CLI exists, start a local daemon
if command -v ipfs >/dev/null 2>&1; then
  nohup ipfs daemon --enable-pubsub-experiment >/tmp/ipfs-daemon.log 2>&1 &
  sleep 2
  echo "ipfs daemon started via local CLI on default ports (api:5001, gateway:8080)" >&2
  exit 0
fi

# 3) Fallback: run dockerized IPFS (ipfs/kubo). Map container 5001->${API_PORT}, 8080->${GATEWAY_PORT}
if command -v docker >/dev/null 2>&1; then
  NAME=${IPFS_DOCKER_NAME:-trustiva-ipfs}
  if docker ps --format '{{.Names}}' | grep -q "^${NAME}$"; then
    echo "dockerized IPFS '${NAME}' already running; reusing" >&2
    exit 0
  fi
  if docker ps -a --format '{{.Names}}' | grep -q "^${NAME}$"; then
    echo "starting existing dockerized IPFS '${NAME}'" >&2
    docker start "$NAME" >/dev/null
  else
    echo "launching dockerized IPFS '${NAME}' (api:${API_PORT}, gateway:${GATEWAY_PORT})" >&2
    docker run -d --name "$NAME" \
      -p ${API_PORT}:5001 \
      -p ${GATEWAY_PORT}:8080 \
      ipfs/kubo:latest >/dev/null
  fi
  # give it a moment
  sleep 3
  echo "dockerized IPFS is up. API=http://127.0.0.1:${API_PORT} GATEWAY=http://127.0.0.1:${GATEWAY_PORT}" >&2
  exit 0
fi

echo "No IPFS CLI or docker available; cannot start IPFS daemon" >&2
exit 0
