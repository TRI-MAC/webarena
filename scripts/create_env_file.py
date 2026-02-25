# The purpose of this script is to create one or more .env file (which will not be checked in) from an environment.yaml file
# Each of the .env files can then be utilized and be injected into either docker-compose or cdk task definition.

import yaml
import json
import argparse
import os

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent) + "/cdk")
from cdk.utils import (
    generate_parameter_hashes_from_object
)

from cdk.configuration.configuration import (
    load_configuration
)

# For now we will just create a single .env file named ".env.environent-name"
# Ultimately, we could have a .env file generated for:
# - the frontend environment variables (env.environment.frontend)
# - the backend environment variables (env.environment.backend)
# - the service connection information (URL + Port) (env.environment.services)
# - the AWS services (env.environment.aws_services) [ only for those services in need of AWS connections ]
# i.e. env.environment.frontend, env.environment.backend, env.environment.service_connections
# Both services will have the frontend and backend environments files
# the service connection can be added to the frontend environment

def recurse_create_object_to_env_file(key_path : list[str], item, object):
    # If we don't have an item, then we return
    if item is None:
        return
    # If we have a string, we have a leaf node
    if not isinstance(item, dict):  
        key_string = "_".join(key_path)
        object[key_string.upper()] = str(item)
        return
    
    # Otherwise, we continue down the tree
    for key in item:
        new_key_path = key_path[:]
        new_key_path.append(key)
        recurse_create_object_to_env_file(new_key_path, item[key], object)

def return_string(key, value):
    return value

def generate_dot_env_from_dict(dictionary : dict[any], env_file_name: str, overwrite : bool = True, is_base_array : bool = False):
    if not overwrite:
        # If we don't want to overwrite (secrets for example), we check if we can open the file
        print("------------")
        print(env_file_name)
        print(os.path.isfile(env_file_name))
        if os.path.isfile(env_file_name):
            # We have a file, so we abort
            print(env_file_name + " and overwrite is disabled so leaving as is")
            return

    file = open(env_file_name, "w")
    # This is really explicitly for secrets but (only 1 base key and ignore base)
    if is_base_array:
        # This for loop will only 
        for key in dictionary:
            for element in dictionary[key].split():
                file.write(element + "=" + '\n')
    else:
        for key in dictionary:
            # print(key)
            # print(dictionary)
            file.write(key + "=" + dictionary[key] + '\n')

    file.close()

def generate_json_file(base_keys : list[str], env_file_name: str):
    object = {}
    for base_key in base_keys:
        if base_key in conf:
            recurse_create_object_to_env_file([base_key], conf[base_key], object)
        else:
             print("Error: No Key ${base_key} found in specified config")

    file = open(env_file_name, "w")
    json.dump(object, file, sort_keys = True, indent = 4,
               ensure_ascii = False)
    file.close() 


parser = argparse.ArgumentParser(description="Argument Parser")
parser.add_argument('--deploy_env', help="environment name", type=str)
args = parser.parse_args()
print(args)
print(args.deploy_env)
if args.deploy_env:
    deploy_env = args.deploy_env
else:
    deploy_env = input("What is the name of environment to deploy? (ex: local / development)")

conf = load_configuration("config/{0}.yaml".format(deploy_env)).__dict__

# We generate the services environment file
app_services_environment_file_path = "config/.env." + deploy_env + ".services.env"
app_service_params = generate_parameter_hashes_from_object(
    input_object=conf,
    base_keys=["app_services", "app_url"],
    param_creation_method=return_string
)
generate_dot_env_from_dict(app_service_params, app_services_environment_file_path)

# The AWS Services environment file
aws_services_environment_file_path = "config/.env." + deploy_env + ".aws_services.env"
aws_services_parameters = generate_parameter_hashes_from_object(
    input_object=conf,
    base_keys=["aws_services"],
    param_creation_method=return_string
)
generate_dot_env_from_dict(aws_services_parameters, aws_services_environment_file_path)

# For each service, we generate it's own configuration and secrets file
services_environments = generate_parameter_hashes_from_object(
    input_object=conf["app_environments"],
    base_keys=[key for key in conf["app_environments"]],
    param_creation_method=return_string,
    separate_hashes=True
)

for service in services_environments:
    file_name = "config/.env." + deploy_env + "." + service +".env"
    generate_dot_env_from_dict(services_environments[service], file_name)
    
# For each service, we generate it's own configuration and secrets file
secret_environments = generate_parameter_hashes_from_object(
    input_object=conf["app_secrets"],
    base_keys=[key for key in conf["app_secrets"]],
    param_creation_method=return_string,
    separate_hashes=True
)

for service in secret_environments:
    file_name = "config/.env." + deploy_env + "." + service + ".secrets.env"
    generate_dot_env_from_dict(secret_environments[service], file_name, overwrite=False, is_base_array=True)

#     generate_dot_env_files_from_dict(conf["app_environments"],[key], "config/.env." + deploy_env + "." + key +".env")
# for key in conf["app_secrets"]:
#     generate_dot_env_files_from_dict(conf["app_secrets"],[key], "config/.env." + deploy_env + "." + key +".secrets.env", overwrite=False)

# generate_dot_env_file([
#     "app_services",
#     "app_url"
# ], services_environment_file_path)
# generate_dot_env_file(["aws_services"], aws_services_environment_file_path)
# generate_dot_env_file(["aws_amplify"], aws_amplify_environment_file_path)

# generate_dot_env_file(["frontend_secrets"], frontend_secrets_file_path, is_base_array=True, overwrite=False)
# generate_dot_env_file(["backend_secrets"], backend_secrets_file_path, is_base_array=True, overwrite=False)


# frontend environment
# if "frontend_env" in conf:
#     frontend_environment_file = open(frontend_environment_file_path, "w")
#     if conf["frontend_env"]:
#         for key in conf["frontend_env"]:
#             line = conf["frontend_env"][key]
#             frontend_environment_file.write(key.upper() + "=" + str(line)+ '\n')
#     frontend_environment_file.close()
# else:
#     print("No frontend specific environment variables found")

# backend environment
# if "backend_env" in conf:
#     backend_environment_file_path = "config/.env." + deploy_env + ".backend"
#     backend_environment_file = open(backend_environment_file_path, "w")
#     if conf["backend_env"]:
#         for key in conf["backend_env"]:
#             line = conf["backend_env"][key]
#             backend_environment_file.write(key.upper() + "=" + str(line)+ '\n')
#     backend_environment_file.close()
# else:
#     print("No backend specific environment variables found")

# # service connections environment file
# if "frontend" not in conf:
#     print("Error: No frontend service description found in specified config")
#     exit(1)
# if "backend" not in conf:
#     print("Error: No backend service description found in specified config")
#     exit(1)

# services_environment_file_path = "config/.env." + deploy_env + ".services"
# services_environment_file = open(services_environment_file_path, "w")
# for key in conf["frontend"]:
#     line = conf["frontend"][key]
#     services_environment_file.write("FRONTEND_" + key.upper() + "=" + str(line) + '\n')

# services_environment_file.write('\n\n')

# for key in conf["backend"]:
#     line = conf["backend"][key]
#     services_environment_file.write("BACKEND_" + key.upper() + "=" + str(line) + '\n')
# services_environment_file.close()

# # AWS Service Connections environment file
# aws_services_environment_file_path = "config/.env." + deploy_env + ".aws_services"
# aws_services_environment_file = open(aws_services_environment_file_path, "w")
# for key in conf["aws_services"]:
#     for service_key in conf["aws_services"][key]:
#         line = conf["aws_services"][key][service_key]
#         aws_services_environment_file.write(key.upper() + "_" + service_key.upper() + "=" + str(line) + '\n')
#     aws_services_environment_file.write('\n\n')
# aws_services_environment_file.close()

# print("Completed - you can now use the following .env files:")
# if 'frontend_environment_file_path' in locals():
#     print(frontend_environment_file_path)

# if 'backend_environment_file_path' in locals():
#     print(backend_environment_file_path)
    
# print(services_environment_file_path)
# print(aws_services_environment_file_path)