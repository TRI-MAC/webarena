#!/bin/bash
# We create the venv if not already there
python3 -m venv scripts/.venv
source scripts/.venv/bin/activate
pip install -r scripts/requirements.txt
python scripts/create_env_file.py --deploy_env local
# Because we are running things from the code itself, we need to ensure that everything is setup to work locally:
cd frontend
yarn
cd ../backend
pip install -r requirements.txt
cd ..
docker compose -f docker-compose.dev.yaml up --build