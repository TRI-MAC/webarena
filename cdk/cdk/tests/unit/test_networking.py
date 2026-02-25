# CDK imports
import aws_cdk as core
import aws_cdk.assertions as assertions
from cdk.cdk_stack import CdkStack
from cdk.networking import Networking, NetworkingParameters
# Other imports
import logging

from cdk.configuration.configuration import (
    load_configuration
)

# Because we are referencing existing resources, we require pulling the configuration for performing the tests
deploy_env = "development" 
conf = load_configuration("../config/{0}.yaml".format(deploy_env))

# VPC Tests


# Logs Bucket

# ALB Tests
############## ALB TESTS ##################
def test_alb_created_has_correct_properties():
    # We are testing the following:
    # - ALB is internet-facing
    # - ALB is in the public subnets of the VPC

    app = core.App()
    stack = CdkStack(app, "cdk",
        env=core.Environment(account=conf.aws.account, region=conf.aws.region),
    )
    template = assertions.Template.from_stack(stack)
    
    public_subnets_ids = [ subnet.subnet_id for subnet in stack.networking.vpc.private_subnets ]

    template.has_resource_properties("AWS::ElasticLoadBalancingV2::LoadBalancer", {
            "Scheme":"internal",
            "Subnets":public_subnets_ids,
            "Type": "application",
        }
    )

def test_alb_security_group_allows_ingress():
    app = core.App()
    stack = CdkStack(app, "cdk",
        env=core.Environment(account=conf.aws.account, region=conf.aws.region),
    )
    template = assertions.Template.from_stack(stack) 

    access_port = 80
    if conf.aws.cert:
        access_port = 443

    template.has_resource_properties("AWS::EC2::SecurityGroup",
        {
            # TODO: VPC Id can't be properly tested using config file here so using stack.vpc.id
            "VpcId": stack.networking.vpc.vpc_id,
            "SecurityGroupIngress": assertions.Match.array_with(
                [
                    # Verify that port 80 is allowed to ingress
                    assertions.Match.object_like(
                        {
                            "CidrIp": "0.0.0.0/0",
                            "FromPort": access_port,
                            "IpProtocol": "tcp",
                            "ToPort": access_port
                        }
                    )
                    # We do not need to open up any other ports, except possibly 443 if/when we do ssl
                    # TODO: if there is SSL, we need to check if port 443 is allowed
                ]
            )
        }
    )

def test_listener_created_redirect():
    app = core.App()
    stack = CdkStack(app, "cdk",
        env=core.Environment(account=conf.aws.account, region=conf.aws.region),
    )
    template = assertions.Template.from_stack(stack) 

    if conf.aws.cert:
        # We check for redirect rule as well
        template.has_resource_properties("AWS::ElasticLoadBalancingV2::Listener", {
            "Port":80,
            "Protocol":"HTTP",
            "DefaultActions": assertions.Match.array_with(
                [
                    assertions.Match.object_like(
                        {
                            "Type": "redirect",
                            "RedirectConfig": {
                                
                            }
                        }
                    )
                ]
            ),
            "LoadBalancerArn": stack.resolve(stack.networking.lb.load_balancer_arn)
        }
    )

def test_service_listener_created():
    app = core.App()
    stack = CdkStack(app, "cdk",
        env=core.Environment(account=conf.aws.account, region=conf.aws.region),
    )
    template = assertions.Template.from_stack(stack) 

    for service in conf.app_services:
        if not conf.app_services[service].attach_to_load_balancer:
            break        

        # No listener rule
        if not conf.app_services[service].base_path:
            break

        template.has_resource_properties("AWS::ElasticLoadBalancingV2::Listener", {
                "Port":conf.app_services[service].container_ports[0],
                "Protocol":"HTTP",
                "DefaultActions": assertions.Match.array_with(
                    [
                        assertions.Match.object_like(
                            {
                                "Type": "forward",
                                "TargetGroupArn": stack.resolve(stack.networking.targets["ECS-" + service].target_group_arn)
                            }
                        )
                    ]
                ),
                "LoadBalancerArn": stack.resolve(stack.networking.lb.load_balancer_arn)
            }
        )

################ Test connections between groups ###########
def test_alb_to_front_end_service_target_group():
    # Test the front end Target group's base configuration
    app = core.App()
    stack = CdkStack(app, "cdk",
        env=core.Environment(account=conf.aws.account, region=conf.aws.region),
    )

    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::ElasticLoadBalancingV2::TargetGroup",
        {
            "Port": 80,
            "TargetType": "ip",
            "Protocol": "HTTP"
        }
    )

def test_alb_to_back_end_service_target_group():
    # Test the Back end Target group's base configuration
    app = core.App()
    stack = CdkStack(app, "cdk",
        env=core.Environment(account=conf.aws.account, region=conf.aws.region),
    )

    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::ElasticLoadBalancingV2::TargetGroup",
        {
            "Port": 80,
            "TargetType": "ip",
            "Protocol": "HTTP"
        }
    )


def test_alb_listener_rule():
    app = core.App()
    stack = CdkStack(app, "cdk",
        env=core.Environment(account=conf.aws.account, region=conf.aws.region),
    )

    template = assertions.Template.from_stack(stack)

    for service in conf.app_services:
        if not conf.app_services[service].attach_to_load_balancer:
            break        

        # No listener rule
        if not conf.app_services[service].base_path:
            break

        path_patterns = [
            conf.app_services[service].base_path + "/*",
            conf.app_services[service].base_path
        ]  
          
        template.has_resource_properties("AWS::ElasticLoadBalancingV2::ListenerRule",
            {
                "Actions": assertions.Match.array_with(
                    [
                        assertions.Match.object_like(
                            {
                                "Type": "forward",
                                "TargetGroupArn": stack.resolve(stack.networking.targets["ECS-" + service ].target_group_arn)
                            }
                        )
                    ]
                ),
                "Priority": 1,
                "Conditions": assertions.Match.array_with(
                    [
                        assertions.Match.object_like(
                            {
                                "Field": "path-pattern",
                                "PathPatternConfig": {
                                    "Values": path_patterns
                                }
                            }
                        )
                    ]
                )
            }
        )
    
def test_alb_to_service_connections():
    app = core.App()
    stack = CdkStack(app, "cdk",
        env=core.Environment(account=conf.aws.account, region=conf.aws.region),
    )
    template = assertions.Template.from_stack(stack) 

    for service in conf.app_services:
        if not conf.app_services[service].attach_to_load_balancer:
            break
        for port in conf.app_services[service].container_ports:
            template.has_resource_properties("AWS::EC2::SecurityGroupEgress",
                {
                    # Because we are using awscpv, the "From Port" property that the ALB will reach out to is the port
                    # on which the container is listening
                    "FromPort": port,
                    "IpProtocol": "tcp",
                    # Because we are using awsvpc, the "To Port" property will be the port the container is listening on,
                    # this bypasses the host port itself.
                    "ToPort": port,
                    # GroupId:
                    # DestinationSecurityGroupId: 
                }
            )