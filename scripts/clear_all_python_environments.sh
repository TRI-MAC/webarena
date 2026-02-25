#!/bin/bash
# Clear all python environments, essentially removing all .venv from the directories in the repo.
# This allows to "start over". This is especially useful when going to and from dev containers

rm -rf scripts/.venv
rm -rf backend/.venv
rm -rf cdk/.venv