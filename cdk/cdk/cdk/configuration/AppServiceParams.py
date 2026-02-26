import yaml
from pydantic import ConfigDict
from pydantic.dataclasses import dataclass
from typing import (
  Optional
)

@dataclass(kw_only=True)
class AppServiceHealthcheckParameters:
    """
    Either path or command have to be specified
    This determins where the service's health check path is

    path: (optional) str
    command: (optional) list[str]
    """

    path: Optional[str] = None
    command: Optional[list[str]] = None

@dataclass(kw_only=True)
class AppServiceEFSServiceConnectionParameters:
    """
    mount_point: str
        Location where to mount the efs storage
    """
    mount_point : str
    access_point_name : str

@dataclass(kw_only=True)
class AppServiceConnectionParameters:
    """
    Service connection Parameters for Fargate Service

    Enables connection to various AWS services automatically
    s3: bool
        Whether to enable access to the s3 bucket
    dynamodb: bool
        Whether to enable access to the dynamodb table
    efs: AppServiceEFSServiceConnectionParameters
        Where to mount the efs storage

    """
    s3: Optional[bool] = False
    dynamodb: Optional[bool] = False
    efs: Optional[AppServiceEFSServiceConnectionParameters] = None
    aurora: Optional[bool] = False
    elasticache: Optional[bool] = False
    amplify : Optional[bool] = False

from dataclasses import field

@dataclass(config=ConfigDict(arbitrary_types_allowed=True), kw_only=True)
class AppServiceResourceAllocation():
    """
    Resource Request for the fargate task

    cpu: cpu request
    memory: Memory Requested
    ephemeral_storage_gib: (optional) Ephemeral storage in GiB (21-200). Required for large images.

    For allowed combinations of CPU / Memory for Fargate please see the following link: https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_ecs.FargateTaskDefinition.html#cpu
    """
    cpu : int = 256
    memory : int = 512
    ephemeral_storage_gib : Optional[int] = None


@dataclass(kw_only=True)
class AppServiceParams:
    directory : str
    healthcheck: AppServiceHealthcheckParameters
    resource_allocation : Optional[AppServiceResourceAllocation] = field(default_factory=AppServiceResourceAllocation)

    service_url: Optional[str] = None
    container_ports: Optional[list[int]] = None
    container_entrypoint: Optional[list[str]] = None
    container_command: Optional[list[str]] = None
    base_path : Optional[str] = None
    route_priority: Optional[int] = 1

    attach_to_load_balancer : Optional[bool] = False
    enabled_service_connections : Optional[AppServiceConnectionParameters] = None