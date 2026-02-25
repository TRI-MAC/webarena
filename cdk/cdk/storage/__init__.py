from constructs import Construct
from pydantic.dataclasses import dataclass
from typing import (
    Optional
)

import re
# CDK imports
from aws_cdk import (
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_efs as efs,
    aws_ec2 as ec2,
    Tags
)

from .efs_storage import (
    EFSStorage,
    EFSParams
)

from .aurora_storage import (
    AuroraParams,
    AuroraStorage
)

from ..fargate_service import (
    FargateService
)

from .elasticache_storage import (
    ElasticacheParams,
    ElasticacheStorage
)


@dataclass(kw_only=True)
class S3Params:
    """
    S3 Parameters

    S3 Parameteres required for the Creation of the S3 Buckets
    """
    existing_s3 : bool
    versioned: Optional[bool] = True
    enforce_ssl: Optional[bool] = True

    data_bucket_resolved_name: Optional[str] = None

@dataclass(kw_only=True)
class DynamoDBParams():
    """
    DynamodB Parameters

    DynamoDB Parameters for creating the dynamodb table

    Parameters:
        table_name : string
            The name of the table to be created
        partition_key : string
            The parition key to be used for the dynamodb table created
    """
    existing_dynamodb : bool
    table_name : str
    partition_key : str

@dataclass(kw_only=True)
class StorageParameters():
    """
    Storage Parameters

    All parameters for the various types of storage available to be created in the stack

    Parameters : 
        s3 (Optional): S3Params | None
            If defined, the S3Params necessary to create the data bucket.
            If None, Data Bucket will not be created
        dynamodb (Optional): DynamoDBParams | None
            If defined, the DynamoDBParams required to create the dynamodb table
            If None, DynamoDB Table will not be created
    """
    s3:  Optional[S3Params] = None
    dynamodb: Optional[DynamoDBParams] = None
    efs: Optional[EFSParams] = None
    aurora: Optional[AuroraParams] = None
    elasticache: Optional[ElasticacheParams] = None

    amplify: Optional[dict] = None

class Storage(Construct):
    """
    Storage Construct

    The storage construct sets up the following infrastructure depending on the provided storage parameters:
    - S3 Data Bucket (if se)
    - 

    Attributes:

    """
    def __init__(self, scope: Construct, id: str, uuid: str,
            storage_parameters: StorageParameters,
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

        self.data_bucket = None
        self.dynamodb_table = None
        self.aurora_storage = None
        self.efs_storage = None
        self.elasticache_storage = None

        if storage_parameters.s3:
            if storage_parameters.s3.existing_s3:
                # We have an s3 bucket resolved
                self.data_bucket = s3.Bucket.from_bucket_name(self, "data-bucket", storage_parameters.s3.data_bucket_resolved_name)
            else:
                #Trying to use the cdk generated name for the data bucket
                self.data_bucket = s3.Bucket(self, "data-bucket",
                    versioned=storage_parameters.s3.versioned,
                    enforce_ssl=storage_parameters.s3.enforce_ssl
                )
                Tags.of(self.data_bucket).add("tri.data.technology","S3")
       

        if storage_parameters.dynamodb:
            if storage_parameters.dynamodb.existing_dynamodb:
                self.dynamodb_table = dynamodb.Table.from_table_name(self, "DynamoDBTable", storage_parameters.dynamodb.table_name) 
            else:
                # 1 DynamoDB Service in Private Subnet

                #Trying to use the cdk generated name for the DynamoDB table
                self.dynamodb_table = dynamodb.Table(self, "DynamoDBTable",
                    partition_key = dynamodb.Attribute(
                        name=storage_parameters.dynamodb.partition_key,
                        type=dynamodb.AttributeType.STRING
                    ),
                )
                Tags.of(self.dynamodb_table).add("tri.data.technology","dynamodb")      

        if storage_parameters.efs:
            self.efs_storage = EFSStorage(self,
                id="EFS-Storage",
                default_vpc=default_vpc,
                efs_parameters=storage_parameters.efs
            )

        if storage_parameters.aurora:
            self.aurora_storage = AuroraStorage(
                self,
                id="Aurora-Storage",
                default_vpc=default_vpc,
                aurora_parameters=storage_parameters.aurora
            )

        if storage_parameters.elasticache:
            self.elasticache_storage = ElasticacheStorage(
                self,
                id="Elasticache-Storage",
                default_vpc=default_vpc,
                elasticache_params=storage_parameters.elasticache
            )

        # We tag the resources appropriately
        Tags.of(self).add("tri.resource.class", "datastorage");
        Tags.of(self).add("tri.data.classification", "datastorage");


    def attach_storage_to_service(self, fargate_service : FargateService) -> None:

        # Attach s3 bucket if necessary
        if self.data_bucket:
            if fargate_service.enabled_service_connections.s3:
                self.data_bucket.grant_read_write(fargate_service.task_definition.task_role)

        if self.dynamodb_table:
            if fargate_service.enabled_service_connections.dynamodb:
                self.dynamodb_table.grant_read_write_data(fargate_service.task_definition.task_role)

        # If we have an efs storage
        if self.efs_storage:
            self.efs_storage.attach_volume_to_service(fargate_service)

        if self.aurora_storage:
            self.aurora_storage.enable_connection_to_service(fargate_service)
            
        if self.elasticache_storage:
            self.elasticache_storage.enable_connection_to_service(fargate_service)            

        return
