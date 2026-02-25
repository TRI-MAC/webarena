from constructs import Construct
from pydantic.dataclasses import dataclass
from typing import Dict

import re
# CDK imports
from aws_cdk import (
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_efs as efs,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    Tags
)

from ..fargate_service import (
    FargateService
)



@dataclass(kw_only=True)
class ExistingEFSParams():
    """
    Existing EFS Params

    EFS Parameters to provide access to an existing efs storage

    Parameters:
        file_system_id: string
            The file system to utilize
    """
    file_system_id: str

@dataclass(kw_only=True)
class EFSAccessPointParams():
    """
    access point params
    """
    name : str
    uid : str
    gid : str
    path : str

@dataclass(kw_only=True)
class EFSParams():
    """
    Elastic File System

    EFS Parameters for creating the efs volume

    Parameters:
        vpcid : str | None (optional)
            the id of the vpc in which to place the new EFS system
        exiting_efs : ExistingEFSParams | None (optional)
            The configuration for an existing efs store which we should mount
        volume_name: string
            The name of the EFS volume to be created
    """
    vpcid: str | None
    existing_efs: ExistingEFSParams | None

    volume_name : str
    access_points : list[EFSAccessPointParams]


class EFSStorage(Construct):
    """
    EFS Storage Construct

    The EFS Storage contruct creates the appropriate AWS resources to enable attaching an EFS volume to the various tasks where they are needed

    Attributes:
    -
    """
    def __init__(self, scope: Construct, id: str,
            efs_parameters: EFSParams,
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
        self.file_system_id = ""
        self.volume_name = efs_parameters.volume_name

        if efs_parameters.existing_efs:
            # We attempt to use an existing efs configuration
            if efs_parameters.existing_efs.file_system_id:
                self.file_system_id = efs_parameters.existing_efs.file_system_id
                self.file_system = efs.FileSystem.from_file_system_attributes(
                    self,
                    id='FileSystem',
                    file_system_id=self.file_system_id
                )
            else:
                raise Exception("Requested to use exiting EFS but no file system id provided")
        else:
            # We don't have an existing efs, so we create a new file system
            if efs_parameters.vpcid:
                # We are explicitly given a vpc id to work with
                self.vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_id=efs_parameters.vpcid)
            else:
                # We use the default vpc
                self.vpc = default_vpc

            self.security_group = ec2.SecurityGroup(
                self,
                id="EFSSecurityGroup",
                vpc=self.vpc,
                allow_all_outbound=True
            )

            self.security_group.add_ingress_rule(
                peer=ec2.Peer.any_ipv4(),
                connection=ec2.Port.tcp(2049),
                description='Allow NFS Connections to EFS'
            )

            self.file_system = efs.FileSystem(
                self,
                id='FileSystem',
                vpc=self.vpc,
                performance_mode=efs.PerformanceMode.GENERAL_PURPOSE,
                vpc_subnets=ec2.SubnetSelection(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    one_per_az=True
                ),
                security_group=self.security_group,
            )
            self.file_system_id = self.file_system.file_system_id

        self.access_points : Dict[str, efs.AccessPoint] = {}
        for access_point_key in efs_parameters.access_points:
            access_point : EFSAccessPointParams = efs_parameters.access_points[access_point_key]
            # We create the access point for the service
            self.access_points[access_point.name] = efs.AccessPoint(
                self,
                id=access_point.name,
                file_system=self.file_system,
                posix_user=efs.PosixUser(
                    uid=access_point.uid,
                    gid=access_point.gid
                ),
                path=access_point.path,
                create_acl=efs.Acl(
                    owner_uid=access_point.uid,
                    owner_gid=access_point.gid,
                    permissions="755"
                )
            )



    def attach_volume_to_service(self, fargate_service : FargateService) -> None:
        """
        attach_volume_to_service

        Attached the volume to the provided Fargate service

        Parameters:
        - fargate_service : FargateService
            The fragate service (created by the stack) to attach the volume to
        """

        if not fargate_service.enabled_service_connections.efs:
            # If the configuration file doesn't specify an efs mount point, then we don't set it up
            return

        # We get the accesspoint
        access_point = self.access_points[fargate_service.enabled_service_connections.efs.access_point_name]

        # We add the volume to the task definition
        fargate_service.task_definition.add_volume(
            name=self.volume_name,
            efs_volume_configuration=ecs.EfsVolumeConfiguration(
                file_system_id=self.file_system.file_system_id,
                transit_encryption='ENABLED',
                authorization_config=ecs.AuthorizationConfig(
                    access_point_id=access_point.access_point_id,
                    iam = 'ENABLED'
                )
            )
        )

        mount_point = ecs.MountPoint(
            container_path=fargate_service.enabled_service_connections.efs.mount_point,
            source_volume= self.volume_name,
            read_only= False
        )

        # We mount the volume
        fargate_service.container.add_mount_points(
            mount_point
        )

        # We give access to the task definition
        self.file_system.grant_root_access(fargate_service.task_definition.execution_role)
        self.file_system.grant_root_access(fargate_service.task_definition.task_role)
        
        self.file_system.connections.allow_default_port_from(fargate_service.service)
        Tags.of(self).add("tri.data.technology","efs")  
        return