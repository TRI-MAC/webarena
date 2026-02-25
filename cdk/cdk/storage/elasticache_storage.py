#WARNING: ELASTICACHE DOESN'T HAVE L2 CONSTRUCTS SO USING L1 CONSTRUCTS
from constructs import Construct
from pydantic.dataclasses import dataclass

from typing import (
    Mapping,
    Optional,
)

import re
# CDK imports
from aws_cdk import (
    aws_elasticache as elasticache,
    aws_ec2 as ec2,
    Tags
)

from ..fargate_service import (
    FargateService
)


@dataclass(kw_only=True)
class ElasticacheParams():
    """
    Aurora RDS Parameters

    Parameters required to create / make use of an Aurora RDS Database

    Parameters:
        vpcid : str | None (optional)
            the id of the vpc in which to place the new Elasticache Store
    """
    vpcid: str | None
    cache_instance_type: Optional[str] = None
    

class ElasticacheStorage(Construct):
    """
    Aurora Storage Construct

    The Aurora Storage contruct creates the appropriate AWS resources to enable the application to use an Aurora Database system

    Attributes:
    - 
    """
    def __init__(self, scope: Construct, id: str,
            elasticache_params: ElasticacheParams,
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
        - elasticache_params : ElasticacheParams
            The parameters for each of the storage infrastructures. This also determines which storage infrastructure is deployed.
        """
        super().__init__(scope, id, **kwargs)

        uuid_len = 8
        if elasticache_params.vpcid:
            # We are explicitly given a vpc id to work with
            self.vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_id=elasticache_params.vpcid)
        else:
            # We use the default vpc
            self.vpc = default_vpc

        if elasticache_params.cache_instance_type:
            self.cache_instance_type = elasticache_params.cache_instance_type
        else:
            self.cache_instance_type = "cache.t3.micro"

        # We start by building the cluster
        # We create a subnet group
        private_subnets = [ subnet.subnet_id for subnet in self.vpc.private_subnets ]
        self.subnet_group = elasticache.CfnSubnetGroup(
            self,
            id="ElasticacheSubnetGroup",
            cache_subnet_group_name="elasticache-subnet-group",
            subnet_ids=private_subnets,
            description="Elasticache subnet group"
        )

        # We create the security group for the elasticache
        self.security_group = ec2.SecurityGroup(
            self,
            id="ElasticacheSecurityGroup",
            vpc=self.vpc,
            allow_all_outbound=True
        )
        
        # We create the elasticache service
        self.cache = elasticache.CfnReplicationGroup(
            self, id="ElasticacheReplicationGroup",
            replication_group_description="elasticache-replication-group",
            num_cache_clusters=1,
            automatic_failover_enabled=False,
            engine="redis",
            cache_node_type=self.cache_instance_type,
            cache_subnet_group_name=self.subnet_group.ref,
            security_group_ids=[self.security_group.security_group_id],
        )
        # TODO: add option for serverless elasticache
        # Limits the cache to $90/month storage
        # Limits the cache to 10 ECPU/s which is 10kb/s cache data entry
        # This means a maximum of 0.034$/s for jobs at full speed
        # self.cache_limits = elasticache.CfnServerlessCache.CacheUsageLimitsProperty(
        #     data_storage=elasticache.CfnServerlessCache.DataStorageProperty(
        #         maximum=1,
        #         unit="GB"
        #     ),
        #     ecpu_per_second=elasticache.CfnServerlessCache.ECPUPerSecondProperty(
        #         maximum=10
        #     )
        # )

        # self.cache = elasticache.CfnServerlessCache(
        #     self,
        #     "ElasticacheCache",
        #     engine="redis",
        #     serverless_cache_name="ServerlessCache",
        #     security_group_ids=[self.security_group.security_group_id],
        #     subnet_ids=private_subnets,
        #     cache_usage_limits=self.cache_limits
        # )

        # We create serverless elasticache with usage limits: max data = 1 GB
        Tags.of(self).add("tri.data.technology","elasticache")  

    def enable_connection_to_service(self, fargate_service : FargateService) -> None:
        """
        enable_connection_to_service

        Enable connection from a fargate service
        
        Parameters:
        - fargate_service : FargateService
            The fragate service (created by the stack) to enable connection from
        """
        if not fargate_service.enabled_service_connections.elasticache:
            return False
        
        self.security_group.connections.allow_from(
            other=fargate_service.service,
            port_range=ec2.Port.tcp(6379)
        )

        return