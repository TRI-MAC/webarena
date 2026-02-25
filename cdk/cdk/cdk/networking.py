from numbers import Number
from typing import Optional, Sequence
from constructs import Construct
import re

# CDK imports
from aws_cdk import (
    aws_certificatemanager as acm,
    aws_elasticloadbalancingv2 as alb,
    aws_ec2 as ec2,
    aws_s3 as s3,
    aws_ecs as ecs,
    Tags,
)

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass
from dataclasses import asdict

from .fargate_service import FargateService
from typing import Optional

@dataclass(kw_only=True)
class NetworkingParameters:
    """
    Parameters for Networking Stack

    Parameters required for Networking stack

    vpcid : string | None
        The ID of the VPC in which to deploy the resources. If none is provided, the account's default VPC will be used.
    cert_arn : string | None
        The ARN of the SSL Certificate to use for the Application Load Balancer. If none is provided, no HTTPS listener or HTTP redirect will be created.
    subnet_ids : list[string] | None
        A list of subnet ARNs that the app should use. If none is provided, all private (with egress) subnet IDs will be chosen
    """

    vpcid: str = None
    cert_arn: str = None
    subnet_ids: Optional[list[str]] = None


@dataclass(config=ConfigDict(arbitrary_types_allowed=True), kw_only=True)
class TargetGroupParams:
    """
    Target Group Parameters

    The parameters required to create the target group associated with the Fargate Service

    Parameters:
        priority : Number (optional)
            The priority with which the loadbalancer will evaluate the created target group
        conditions : Sequence[alb.ListenerCondition] (optional)
            Conditions for the load balancer rule created
    """

    priority: Number = None
    conditions: Optional[Sequence[alb.ListenerCondition]] = None


class Networking(Construct):
    """
    Networking Construct

    The networking construct sets up the following infrastructure:
    - Application Load Balancer (ALB)
    - Log bucket for ALB
    - HTTPS Listener (if SSL Certificate ARN is provided)
    - HTTP Forwarder (if SSL Certificate ARN is provided)
    - HTTP Listener (if no SSL Certificate ARN is provided)

    Attributes:
        vpc : aws_ec2.Vpc
            The VPC which was resolved based on provided vpcid (or default vpc if no vpcid was provided)
        lb : aws_elasticloadbalancingv2.ApplicationLoadBalancer
            The Application Load Balancer created in the VPC
        logs_bucket : aws_s3.Bucket
            The bucket created for the ALB to log into
        listener : aws_elasticloadbalancingv2.ApplicationListener
            The Listener associated with the load balancer. This will be https if certificate is provided, otherwise http
        redirect : aws_elasticloadbalancingv2.ApplicationListener
            The Redirect rule for redirecting HTTP traffice to HTTPS. None if no certificate is provided.
        cert : aws_certificatemanager.Certificate |  None
            The SSL certificate if any
        lb_url : string
            The URL for the Application Load Balancer
        targets :
            Targets associated with the listener by id

    """

    vpc: ec2.Vpc
    lb: alb.ApplicationLoadBalancer
    logs_bucket: s3.Bucket
    listener: alb.ApplicationListener
    redirect: alb.ApplicationListener | None
    cert: acm.Certificate | None
    lb_url: str

    def __init__(
        self,
        scope: Construct,
        id: str,
        app_name: str,
        networking_params: NetworkingParameters,
        **kwargs
    ) -> None:
        """
        Creates the networking stack

        Creates the networking stack with the networking components listed above

        Parameters:
            scope: Construct
                The parent construct in which the networking construct will be deployed.
            id : string
                Reference for the networking stack
            app_name : string
                Name of the application.
            networking_params : NetworkingParameters
                Parameters required for Networking stack
        """

        super().__init__(scope, id, **kwargs)

        if networking_params.vpcid:
            self.vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_id=networking_params.vpcid)
        else:
            self.vpc = ec2.Vpc.from_lookup(self, "VPC", is_default=True)

        if networking_params.subnet_ids:
            selected_subnets = []
            for subnet_id in networking_params.subnet_ids:
                selected_subnets.append(
                    ec2.Subnet.from_subnet_id(self, subnet_id, subnet_id)
                )
            self.subnet_selection = ec2.SubnetSelection(subnets=selected_subnets)
        else:
            self.subnet_selection = ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS, one_per_az=True
            )

        # Load Balancer internet facing
        # We might want to transition from port-based to path-based routing for ease of deployment / use
        self.lb = alb.ApplicationLoadBalancer(
            self,
            "ALB",
            vpc=self.vpc,
            internet_facing=False,
            vpc_subnets=self.subnet_selection,
        )

        self.logs_bucket = s3.Bucket(self, "logs-bucket", enforce_ssl=True)

        # We setup the log access buckets
        self.lb.log_access_logs(bucket=self.logs_bucket)

        # Create the listeners for the various ports
        # If we have an ssl certificate, we setup 443 listener as the base one and 80 as a redirect to 443
        if networking_params.cert_arn:
            self.cert = acm.Certificate.from_certificate_arn(
                self, "Certificate", networking_params.cert_arn
            )
            self.listener = self.lb.add_listener(
                "HTTPS Listener",
                port=443,
                open=True,
                ssl_policy=alb.SslPolicy.RECOMMENDED_TLS,
                protocol=alb.ApplicationProtocol.HTTPS,
            )
            # Add certificate to 443 listener
            self.listener.add_certificates("dso-cert", [self.cert])

            # Setup redirect rule for port 80 listener
            self.redirect = self.lb.add_listener(
                "HTTP Listener",
                port=80,
                open=True,
                protocol=alb.ApplicationProtocol.HTTP,
                default_action=alb.ListenerAction.redirect(
                    port="443", permanent=True, protocol="HTTPS"
                ),
            )
        else:
            self.listener = self.lb.add_listener(
                "HTTP Listener",
                port=80,
                open=True,
                protocol=alb.ApplicationProtocol.HTTP,
            )
            self.redirect = None
            self.cert = None

        # We create the load balancer parameter group and set the parameters for the frontend and backend service urls
        connection_prefix = "http"
        if networking_params.cert_arn:
            connection_prefix = connection_prefix + "s"

        self.lb_url = connection_prefix + "://" + self.lb.load_balancer_dns_name

        self.targets = {}

        # We tag the resources appropriately
        Tags.of(self).add("tri.resource.class", "infrastructure")

    def add_fargate_target_group(self, id: str, fargate_service: FargateService):
        """
        Add Fargate Target Group

        Adds the provided fargate service to the load balancer as a target group and configures the appropriate healthcheck.

        Arguments:
            id : str
                The id of the constructs to be created. Must be unique accross the stack
            fargate_service : FargateService
                The fargate service to add to the listener.
            target_group_params : TargetGroupParams (optional)
                specific parameters to add to the target group
        """

        if not fargate_service.attach_to_load_balancer:
            # We don't attach
            return

        # If we don't have taget group params we default to the defaults
        if fargate_service.route_priority and fargate_service.base_path:
            path_patterns = [
                fargate_service.base_path + "/*",
                fargate_service.base_path,
            ]

            target_group_params = TargetGroupParams(
                priority=fargate_service.route_priority,
                conditions=[alb.ListenerCondition.path_patterns(path_patterns)],
            )
        else:
            target_group_params = TargetGroupParams()

        new_targets = self.listener.add_targets(
            id,
            protocol=alb.ApplicationProtocol.HTTP,
            targets=[fargate_service.service],
            **asdict(target_group_params)
        )

        new_targets.configure_health_check(
            path=fargate_service.healthcheck_path,
            protocol=alb.Protocol.HTTP,
        )

        self.targets[id] = new_targets
