"""
The configuration file will provide configuration dataclasses, structures and methods to load the config file and access it properly
The main goal is to simplify the process and use a library / set of libraries that are more widely supported:
- pydantic
- yaml
"""

import yaml
from pydantic.dataclasses import dataclass
from typing import Optional

from .AppServiceParams import AppServiceParams

from ..storage import StorageParameters


@dataclass(kw_only=True)
class ECRParams:
    url: str
    region: str


@dataclass(kw_only=True)
class AWSParams:
    account: str
    region: str
    vpcid: str
    cert: str
    ecr: ECRParams
    subnet_ids: Optional[list[str]] = None


@dataclass(kw_only=True)
class GithubActionsParams:
    aws_region: str
    aws_deploy_role: str


@dataclass(kw_only=True)
class Configuration:
    """
    The configuration dataclass represents the expected configuration file
    """

    aws: AWSParams
    github_actions: GithubActionsParams

    env: str
    app_name: str
    app_url: Optional[str]

    tags: dict[str, str]

    app_services: dict[str, AppServiceParams]

    app_environments: Optional[dict[str, dict[str, str]]]

    app_secrets: Optional[dict[str, list[str]]]

    aws_services: Optional[StorageParameters]


def load_configuration(file: str):
    with open(file) as stream:
        try:
            the_yaml = yaml.safe_load(stream)
            print(the_yaml)
            return Configuration(**the_yaml)
        except yaml.YAMLError as exc:
            print(exc)


# AWS Amplify should be separate as it needs to be accessed by the frontend
# Optional: if used will create a cognito user pool for use with Amplify
# aws_amplify:
# enabled: false
# If enabled is true, the auth: region: where to create the user pool must be set
# auth:
#   region: "us-east-1"
