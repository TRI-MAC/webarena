#!/bin/bash
# To Run the CDK Tests we start by installing the requirements
echo "Changing to CDK Directory"
cd ${PWD}/cdk
python3 -m venv .venv
# We activate the environment first
source .venv/bin/activate
# Then we install the requirements
pip install -r requirements.txt
# Finally we run the diff
cdk diff