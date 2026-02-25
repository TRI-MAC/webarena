#!/bin/bash
# We create the venv if not already there
python3 -m venv scripts/.venv
source scripts/.venv/bin/activate
pip install -r scripts/requirements.txt
python scripts/create_env_file.py --deploy_env local
docker compose up --build