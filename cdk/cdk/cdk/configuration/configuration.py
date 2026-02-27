"""
The configuration file will provide configuration dataclasses, structures and methods to load the config file and access it properly
"""

import yaml
from dataclasses import field
from pydantic.dataclasses import dataclass
from typing import Optional


@dataclass(kw_only=True)
class AWSParams:
    account: str
    region: str
    vpcid: str


@dataclass(kw_only=True)
class GithubActionsParams:
    aws_region: str
    aws_deploy_role: str


@dataclass(kw_only=True)
class EC2InstanceParams:
    ami_id: str
    instance_type: str = "t3a.xlarge"
    volume_size_gib: int = 1000
    key_pair_name: Optional[str] = None
    open_ports: list[int] = field(default_factory=lambda: [7770, 7780])


@dataclass(kw_only=True)
class Configuration:
    """
    The configuration dataclass represents the expected configuration file
    """

    aws: AWSParams
    github_actions: GithubActionsParams

    env: str
    app_name: str

    tags: dict[str, str]

    ec2_instance: EC2InstanceParams


def load_configuration(file: str):
    with open(file) as stream:
        try:
            the_yaml = yaml.safe_load(stream)
            print(the_yaml)
            return Configuration(**the_yaml)
        except yaml.YAMLError as exc:
            print(exc)
