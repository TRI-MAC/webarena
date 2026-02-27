from typing import Optional
from constructs import Construct

from aws_cdk import (
    aws_ec2 as ec2,
    Tags,
)

from pydantic.dataclasses import dataclass


@dataclass(kw_only=True)
class NetworkingParameters:
    """
    Parameters for Networking

    vpcid : string | None
        The ID of the VPC in which to deploy the resources.
        If none is provided, the account's default VPC will be used.
    subnet_ids : list[string] | None
        Specific subnet IDs to use. If none, public subnets are used.
    """

    vpcid: str = None
    subnet_ids: Optional[list[str]] = None


class Networking(Construct):
    """
    Networking Construct

    Resolves the VPC for the stack.

    Attributes:
        vpc : aws_ec2.IVpc
            The VPC resolved from vpcid (or default VPC if no vpcid provided)
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        networking_params: NetworkingParameters,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        if networking_params.vpcid:
            self.vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_id=networking_params.vpcid)
        else:
            self.vpc = ec2.Vpc.from_lookup(self, "VPC", is_default=True)

        Tags.of(self).add("tri.resource.class", "infrastructure")
