from typing import (
    Mapping,
    Optional,
    Sequence
)
from constructs import Construct


# CDK imports
from aws_cdk import (
    aws_ecr as ecr,
    aws_ecs as ecs,
    aws_logs as logs,
    aws_ssm as ssm,
    aws_iam as iam,
    RemovalPolicy,
    Tags,
    Duration,
)

from .configuration.AppServiceParams import (
    AppServiceParams
)

from .adot_configuration import ADOTConfiguration

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

@dataclass(config=ConfigDict(arbitrary_types_allowed=True), kw_only=True)
class FargateServiceParameters(AppServiceParams):
    """
    Parameters for Fargate Service

    Parameters required for Fargate Service including ECR Repository
    identifier : string
        The identifier of the service - this will be used for naming
    directory : string
        The directory in which the code can be found (for building and pushing images)
    app_name : string
        the name of the app - this will be used for naming
    environment : string
        Then environment name for the service
    container_command : Optional(string)
        The command to run in the container, if none is defined will run the CMD from the docker image
    container_ports : (Optional) list int
        The port on which the application is listening.
    healthcheck : FargateServiceHealthcheckParameters
        The  Healthcheck command to run
    image_tag : string

    attach_to_load_balancer: (optional) bool - default false
        Whether to expose this service through the external load balancer

    secrets : Mapping[str, ecs.Secret] (optional parameter - defaults to None)
    log_group : logs.LogGroup (optional parameter - defaults to None)
    
    """
    identifier : str
    app_name : str
    image_tag : str
    environment : str
    secrets : Optional[Mapping[str, ecs.Secret]] = None
    log_group : Optional[logs.LogGroup] = None


class FargateService(Construct):
    """
    Fargate Service Construct

    The networking construct sets up the following infrastructure:
    - ECR Repository
    - ECS Service

    Attributes:
    - healthcheck : str
        The path for the service's healthcheck
    - repository : ecr.Repository
        The resolved ecr Repository
    - task_definition : ecs.FargateTaskDefinition
        The created fargate task definition
    - container : ecs.Container
        The container that will be run
    - service : ecs.FargateService
        The created fargate service
    """

    def __init__(self, scope: Construct, id: str, app_name : str, cluster : ecs.Cluster, service_params : FargateServiceParameters, **kwargs) -> None:
        """
        Creates the Fargate Service

        Creates the fargate service with the components listed above
        
        Parameters:
            scope: Construct
                The parent construct in which the service construct will be deployed.
            id : string
                Reference for the service construct
            app_name : string
                Name of the application. 
            service_params : FargateServiceParameters
                Parameters required for Service Construct
        """

        super().__init__(scope, id, **kwargs)
        self.attach_to_load_balancer = service_params.attach_to_load_balancer
        self.healthcheck_path = service_params.healthcheck.path
        self.enabled_service_connections = service_params.enabled_service_connections

        # We setup automatic naming of the various aspects of the application
        self.repository_name =  service_params.app_name + "/" + service_params.identifier.lower()
        self.service_name = service_params.app_name + "-" + service_params.identifier.lower() + "-" + service_params.environment + "-service"
        self.container_name = service_params.identifier.lower()

        self.repository = ecr.Repository.from_repository_name(self,"Repository", repository_name = self.repository_name)
        # We create the task definition
        task_def_kwargs = dict(cpu=service_params.resource_allocation.cpu, memory_limit_mib=service_params.resource_allocation.memory)
        if service_params.resource_allocation.ephemeral_storage_gib is not None:
            task_def_kwargs["ephemeral_storage_gib"] = service_params.resource_allocation.ephemeral_storage_gib
        self.task_definition = ecs.FargateTaskDefinition(self, "Task", **task_def_kwargs)

        # We set to retain the task definition on removal - this allows to keep track of previous versions to easily revert
        self.task_definition.apply_removal_policy(RemovalPolicy.RETAIN)

        self.base_path = service_params.base_path
        self.route_priority = service_params.route_priority
        self.log_group = service_params.log_group

        # We tag the task definition with the image tag
        Tags.of(self.task_definition).add("image-tag", service_params.image_tag, include_resource_types=["AWS::ECS::TaskDefinition"])
        self.container_command = None
        if service_params.container_command:
            self.container_command = service_params.container_command

        self.container_entrypoint = None
        if service_params.container_entrypoint:
            self.container_entrypoint = service_params.container_entrypoint

        self.container_port_mapings = None
        if service_params.container_ports:
            self.container_port_mapings = []
            for port in service_params.container_ports:
                self.container_port_mapings.append(
                    ecs.PortMapping(
                        name = self.service_name,
                        container_port = port
                    )
                )
        
        self.healthcheck_command=["CMD-SHELL"]
        if service_params.healthcheck.path:
            url = "http://localhost"
            if service_params.container_ports:
                url = url + ":" + str(service_params.container_ports[0])
            self.healthcheck_command.append("curl -f " + url + service_params.healthcheck.path + " || exit 1")
        else:
            command_array = service_params.healthcheck.command
            self.healthcheck_command += command_array


        # Now we create the service container
        self.container = self.task_definition.add_container(self.container_name,
            #  TODO: verify if we use from registry or if we simply build the image when deploying infra
            # This assumes that the ecr repository is in the same region and account as the deployed infra
            image=ecs.ContainerImage.from_ecr_repository(self.repository, service_params.image_tag),
            port_mappings = self.container_port_mapings,
            environment = {
                "HOSTNAME": "::"
            },
            entry_point = self.container_entrypoint,
            command = self.container_command,
            readonly_root_filesystem = False,
            # For the secrets, we have the parameters that we created
            secrets = service_params.secrets,
            logging = ecs.AwsLogDriver(                       
                log_group = self.log_group,
                stream_prefix = app_name + "-" + self.service_name
            ),
            health_check = ecs.HealthCheck(
                command=self.healthcheck_command,
                timeout=Duration.seconds(60),
                # Allow enough startup time for heavier services (e.g. Magento + embedded MySQL)
                start_period=Duration.minutes(5)
            )
        )


        # And we add the proper permissions ot the task role
        # self.task_definition.task_role.add_managed_policy()


        self.service = ecs.FargateService(self, "Service",
            cluster = cluster,
            task_definition = self.task_definition,
            service_name = self.service_name,
            circuit_breaker=ecs.DeploymentCircuitBreaker(
                enable=True,
                rollback=True
            ),
            enable_execute_command=True,
            # Give the container time to pass its first ALB health check before
            # ECS considers the deployment unhealthy (matches container start_period)
            health_check_grace_period=Duration.minutes(5)
        )


        Tags.of(self).add("tri.resource.class", "application");


    def addOtel(self, adot_configuration : ADOTConfiguration):

        # We add ability to send the metrics to prometheus here
        self.task_definition.task_role.attach_inline_policy(iam.Policy(self, "WriteToPrometheus",
            statements= [
                iam.PolicyStatement(
                    actions=["aps:RemoteWrite"],
                    effect=iam.Effect.ALLOW,
                    resources=["arn:aws:aps:" + adot_configuration.region + ":" + adot_configuration.account + ":workspace/" + adot_configuration.workspace_id]
                ),
                iam.PolicyStatement(
                    actions=["xray:PutTraceSegments"],
                    effect=iam.Effect.ALLOW,
                    resources=["*"]

                )
            ]
        ))

        # We also add the AWS OTEL Collector
        self.task_definition.add_container("otel-container",
            container_name="aws-otel-collector",
            image=ecs.ContainerImage.from_registry("public.ecr.aws/aws-observability/aws-otel-collector:latest"),
            essential=True,
            command=["--config=/etc/ecs/ecs-custom-config.yaml"],
            health_check=ecs.HealthCheck(
                command=["CMD","/healthcheck" ],
                # interval=Duration.seconds(6),
                # timeout=Duration.seconds(5),
                retries=5,
                start_period=Duration.seconds(1)
            ),
            # port_mappings=[
            #     ecs.PortMapping(container_port=4317,host_port=4317, protocol=ecs.Protocol.UDP),
            #     ecs.PortMapping(container_port=4318,host_port=4318, protocol=ecs.Protocol.UDP),
            #     ecs.PortMapping(container_port=2000,host_port=2000, protocol=ecs.Protocol.UDP),
            #     ecs.PortMapping(container_port=13133,host_port=13133, protocol=ecs.Protocol.UDP),
            # ],
            logging= ecs.AwsLogDriver(                       
                log_group=self.log_group,
                stream_prefix=self.service_name + "-otel-collector"
            ),
            environment={
                "AOT_CONFIG_CONTENT": adot_configuration.adot_config_parameter.string_value
            }
        )
