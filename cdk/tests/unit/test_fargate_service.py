# CDK imports
import aws_cdk as core
import aws_cdk.assertions as assertions
from cdk.cdk_stack import CdkStack

# Other imports
from cdk.utils import (
    sanitize_name
)

from cdk.configuration.configuration import (
    load_configuration
)

# Because we are referencing existing resources, we require pulling the configuration for performing the tests
deploy_env = "development" 
conf = load_configuration("../config/{0}.yaml".format(deploy_env))
conf.app_name = sanitize_name(conf.app_name)

# example tests. To run these tests, uncomment this file along with the example
# resource in cdk/cdk_stack.py

    
################ ECS Tests ###################

def test_ecs_cluster_presence():
    app = core.App()
    stack = CdkStack(app, "cdk",
        env=core.Environment(account=conf.aws.account, region=conf.aws.region),
    )
    template = assertions.Template.from_stack(stack)
    template.has_resource_properties("AWS::ECS::Cluster",
        {

        }
    )

def test_ecs_services():
    app = core.App()
    stack = CdkStack(app, "cdk",
        env=core.Environment(account=conf.aws.account, region=conf.aws.region),
    )
    template = assertions.Template.from_stack(stack)
    private_subnets_ids = [ subnet.subnet_id for subnet in stack.networking.vpc.private_subnets ]        
    for service in conf.app_services:
        load_balancers = None
        if conf.app_services[service].attach_to_load_balancer:
            ports_open = []
            for port in conf.app_services[service].container_ports:
                ports_open.append(
                    assertions.Match.object_like(
                        {
                            "ContainerName": service.lower(),
                            "ContainerPort": port,
                        }
                    )
                )
            load_balancers=assertions.Match.array_with(
                ports_open
            )
            
        # For each service we check if the template defined the service itself
        service_name = conf.app_name + "-" + service.lower() + "-" + conf.env + "-service"
        template.has_resource_properties("AWS::ECS::Service",
            {
                "LaunchType": "FARGATE",
                "ServiceName": service_name,
                "NetworkConfiguration": {
                    "AwsvpcConfiguration": assertions.Match.object_like(
                        {
                            "AssignPublicIp": "DISABLED",
                            # TODO: add check for SecurityGroups
                            "Subnets": private_subnets_ids,
                        }
                    )
                },
                "LoadBalancers": load_balancers
            }
        )

def test_ecs_security_groups():
    app = core.App()
    stack = CdkStack(app, "cdk",
        env=core.Environment(account=conf.aws.account, region=conf.aws.region),
    )
    template = assertions.Template.from_stack(stack)

    # Test that the front end service security group is present
    for service in conf.app_services:
        group_description = "cdk/" + conf.app_name + "-" + conf.env + "-" + service + "Service" + "/Service/SecurityGroup"
        template.has_resource_properties("AWS::EC2::SecurityGroup", {
            "GroupDescription": group_description
        })
    return

def test_ecs_task_definitions():
    app = core.App()
    stack = CdkStack(app, "cdk",
        env=core.Environment(account=conf.aws.account, region=conf.aws.region)
    )
    template = assertions.Template.from_stack(stack)

    for service in conf.app_services:

        secrets_object = {
            "Name": "APP_SERVICES_BACKEND_SERVICE_URL"
        }

        port_mappings = []
        service_name = conf.app_name + "-" + service.lower() + "-" + conf.env + "-service"
        for port in conf.app_services[service].container_ports:
            port_mappings.append(
                {
                    "ContainerPort": port,
                    "Name": service_name,
                    "Protocol": "tcp"
                }
            )

        template.has_resource_properties("AWS::ECS::TaskDefinition",
            {
                "NetworkMode": "awsvpc",
                "RequiresCompatibilities": [
                    "FARGATE"
                ],
                "ContainerDefinitions": assertions.Match.array_with(
                    [
                        assertions.Match.object_like(
                            {
                                "Image": assertions.Match.object_like(
                                    {
                                        "Fn::Join": [
                                            "",
                                            assertions.Match.array_with(
                                                [
                                                    conf.aws.account + ".dkr.ecr." + conf.aws.ecr.region + ".",
                                                    {"Ref": "AWS::URLSuffix"},
                                                    "/" + conf.app_name + "/" + service.lower() + ":latest"
                                                ]
                                            )
                                        ]
                                    }
                                ),
                                "Name": service.lower(),
                                "PortMappings": port_mappings,
                                "Environment": assertions.Match.array_with(
                                    [
                                        assertions.Match.object_like(
                                            {
                                                "Name": "HOSTNAME",
                                                "Value": "::"
                                            }
                                        )
                                    ]
                                ),
                                # We test a subset of the secrets to see if they are present
                                "Secrets": assertions.Match.array_with([
                                    assertions.Match.object_like(
                                        secrets_object
                                    )
                                ])
                            }
                        )
                    ]
                )
            }
        )

def test_ecs_service_roles():
    app = core.App()
    stack = CdkStack(app, "cdk",
        env=core.Environment(account=conf.aws.account, region=conf.aws.region),
    )
    template = assertions.Template.from_stack(stack)
    for service in conf.app_services:
        # We get the role name to check that the role is actually present
        role_name = stack.resolve(stack.services[service].task_definition.task_role.role_name)["Ref"]
        template.template_matches(
            {
                "Resources": {
                    role_name: {
                        "Properties": {
                            "AssumeRolePolicyDocument": {
                                "Statement": [
                                    {
                                        "Action": "sts:AssumeRole",
                                        "Effect": "Allow",
                                        "Principal": {
                                            "Service": "ecs-tasks.amazonaws.com"
                                        }
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        )