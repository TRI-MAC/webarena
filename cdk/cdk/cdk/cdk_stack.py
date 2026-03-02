from aws_cdk import (
    Stack,
    CfnOutput,
    RemovalPolicy,
    Tags,
    aws_logs as logs,
)

from constructs import Construct

from .parameters import Parameters
from .networking import Networking
from .ec2_service import WebArenaEC2


class CdkStack(Stack):
    """
    CDK Stack for WebArena

    Deploys a single EC2 instance from the WebArena AMI with shopping
    and shopping_admin services on ports 7770 and 7780.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.parameters = Parameters(self, id=construct_id + "-parameters")
        base_id = self.parameters.app_name + "-" + self.parameters.deploy_env

        # Apply stack-level tags
        for key, value in self.parameters.tags.items():
            Tags.of(self).add(key, value)

        # VPC
        self.networking = Networking(
            self,
            id=base_id + "-Networking",
            networking_params=self.parameters.networking_parameters,
        )

        # CloudWatch log groups (30-day retention; destroyed with stack)
        log_group_prefix = f"/webarena/{self.parameters.deploy_env}"
        for suffix in ["startup", "shopping", "shopping_admin"]:
            logs.LogGroup(
                self,
                f"LogGroup-{suffix}",
                log_group_name=f"{log_group_prefix}/{suffix}",
                retention=logs.RetentionDays.ONE_MONTH,
                removal_policy=RemovalPolicy.DESTROY,
            )

        # EC2 instance from WebArena AMI
        self.ec2 = WebArenaEC2(
            self,
            id=base_id + "-EC2",
            vpc=self.networking.vpc,
            ami_id=self.parameters.ec2_instance.ami_id,
            params=self.parameters.ec2_instance,
            log_group_prefix=log_group_prefix,
        )

        CfnOutput(
            self,
            "InstanceId",
            value=self.ec2.instance.instance_id,
            description="WebArena EC2 instance ID — look up public IP in EC2 console",
        )
