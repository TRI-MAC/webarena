# The purpose of this script is to create one or more .env file (which will not be checked in) from an environment.yaml file
# Each of the .env files can then be utilized and be injected into either docker-compose or cdk task definition.

import json
import argparse
import os
import boto3
import sys

sys.path.append(str(Path(__file__).parent.parent) + "/cdk")
from cdk.utils import (
    sanitize_name
)

from cdk.cdk.configuration.configuration import (
    load_configuration
)


parser = argparse.ArgumentParser(description="Argument Parser")
parser.add_argument('--deploy_env', help="environment name", type=str)
args = parser.parse_args()
print(args)
print(args.deploy_env)
if args.deploy_env:
    deploy_env = args.deploy_env
else:
    deploy_env = input("What is the name of environment to deploy? (ex: local / development)")
# file_format = input("Is this for secrets manager deployment? (Yes / no)")

conf = load_configuration("config/{0}.yaml".format(deploy_env))

# For each service in app_services, we create a new ecr
base_repo_name = sanitize_name(conf["app_name"])
for service in conf["app_services"]:
    repository_name = base_repo_name + "-" + service.lower()
    print(repository_name)
    
# aws ecr describe-repositories --repository-names ${REPO_NAME} || aws ecr create-repository --repository-name ${REPO_NAME}