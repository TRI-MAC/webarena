#!/bin/bash
# We create the venv if not already there
python3 -m venv scripts/.venv
source scripts/.venv/bin/activate
echo "Stopping the containers - "
docker compose -f docker-compose.dev.yaml down