from constructs import Construct
from pydantic.dataclasses import dataclass


import re
# CDK imports
from aws_cdk import (
    aws_rds as rds,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    Tags
)

from ..fargate_service import (
    FargateService
)

@dataclass(kw_only=True)
class ExistingAuroraParams():
    """
    Existing Auror Params

    Aurora RDS Parameters to provide access to an existing rds cluster / db

    Parameters:
        aurora_id: string
            The id of the database
    """
    aurora_id: str


@dataclass(kw_only=True)
class AuroraParams():
    """
    Aurora RDS Parameters

    Parameters required to create / make use of an Aurora RDS Database

    Parameters:
        vpcid : str | None (optional)
            the id of the vpc in which to place the new EFS system
        existing_aurora : ExistingAuroraParams | None (optional)
            The configuration for an existing aurora database
    """
    vpcid: str | None
    existing_aurora: ExistingAuroraParams | None


class AuroraStorage(Construct):
    """
    Aurora Storage Construct

    The Aurora Storage contruct creates the appropriate AWS resources to enable the application to use an Aurora Database system

    Attributes:
    -
    """
    def __init__(self, scope: Construct, id: str,
            aurora_parameters: AuroraParams,
            default_vpc: ec2.Vpc,
            **kwargs
    ) -> None:
        """
        Creates the storage construct

        Create the storage infrastructure based on the storage_parameters and app_name.

        Parameters:
        - id : str
            Id of the storage construct
        - app_name : str
            The name of the app (also the stack name)
        - storage_parameters : StorageParameters
            The parameters for each of the storage infrastructures. This also determines which storage infrastructure is deployed.
        """
        super().__init__(scope, id, **kwargs)

        uuid_len = 8

        if aurora_parameters.vpcid:
            # We are explicitly given a vpc id to work with
            self.vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_id=aurora_parameters.vpcid)
        else:
            # We use the default vpc
            self.vpc = default_vpc

        self.cluster = rds.DatabaseCluster(self, "AuroraCluster",
            engine=rds.DatabaseClusterEngine.aurora_mysql(version=rds.AuroraMysqlEngineVersion.VER_3_06_1),
            credentials=rds.Credentials.from_generated_secret("clusteradmin"),  # Optional - will default to 'admin' username and generated password
            writer=rds.ClusterInstance.provisioned("writer",
                publicly_accessible=False
            ),
            readers=[
                rds.ClusterInstance.provisioned("reader", promotion_tier=1)
            ],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            vpc=self.vpc
        )

    def enable_connection_to_service(self, fargate_service : FargateService) -> None:
        """
        enable_connection_to_service

        Enable connection from a fargate service

        Parameters:
        - fargate_service : FargateService
            The fragate service (created by the stack) to enable connection from
        """

        if not fargate_service.enabled_service_connections.aurora:
            # If the configuration file doesn't specify aurora usage, we don't enable it
            return
        
        # If the service connection is required, we also grant the service access to the secret
        cluster_secret = ecs.Secret.from_secrets_manager(self.cluster.secret)
        fargate_service.container.add_secret(name="AWS_SERVICES_AURORA_CLUSTER_SECRET",secret=cluster_secret)
        # self.cluster.grant_connect(fargate_service.task_definition.execution_role)

        self.cluster.connections.allow_default_port_from(fargate_service.service)


        return