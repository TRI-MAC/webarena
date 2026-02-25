# CDK imports
from aws_cdk import (
    # Duration,
    Stack,
    aws_ecs as ecs,
    aws_elasticloadbalancingv2 as alb,
    aws_logs as logs,
    Tags,
    Fn
)

from constructs import Construct


# Construct imports
from .parameters import Parameters
from .storage import Storage
from .networking import (
    Networking,
    TargetGroupParams
)
from .cognito import Cognito

from .fargate_service import FargateService
from .adot_configuration import ADOTConfiguration

class CdkStack(Stack):
    """
    CDK Stack

    This stack is responsible for deploying the various infrastructure necessary to running the web app.

    """
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        """
        CDK Stack

        Parameters:
        - scope : Construct
            The scope in which to deploy the stack. This will be an application for example.
        - construct_id : str
            The id of the generated stack construct
        """
        # Note that as we create the various structures within the stack, we expose them as objects of the class
        # This enables using them later in the code (i.e. self.vpc) and during testing (stack.vpc)
        super().__init__(scope, construct_id, **kwargs)

        # Get configuration and define some constants for the stack
        self.parameters = Parameters(self, id=construct_id + "-parameters")
        base_id = self.parameters.app_name + "-" + self.parameters.deploy_env

        uuid = Fn.select(0,Fn.split('-', Fn.select(2, Fn.split("/", self.stack_id))))
        self.parameters.set_uuid(uuid)

        ######################### Networking aspects ############################
        # The networking aspects include getting the vpc, etc...
        self.networking = Networking(self,
            id= base_id + "-Networking",
            app_name=self.parameters.app_name,
            networking_params=self.parameters.networking_parameters
        )

        # Update the parameters based on networking components
        self.parameters.set_networking_parameters(self.networking)

        ######################### Storage Components ############################
        self.storage = Storage(self,
            id=base_id + "-storage",
            uuid=self.parameters.uuid,
            storage_parameters = self.parameters.storage_parameters,
            default_vpc = self.networking.vpc
        )

        # Update the parameters based on storage components
        self.parameters.set_storage_params(self.storage)


        ######################### COGNITO USER POOL ######################
        if self.parameters.cognito_parameters.enabled:
            self.cognito = Cognito(self, base_id + "-Cognito", self.parameters.cognito_parameters)

            # Set the parameters related to the new user pool
            self.parameters.set_user_pool_information(user_pool_id=self.cognito.user_pool.user_pool_id, user_pool_client_id=self.cognito.user_pool_client.user_pool_client_id)

        ######################### LOG GROUP ######################
        # We create a log group for the various logging things
        self.log_group = logs.LogGroup(self, base_id + '-LogGroup')
        Tags.of(self.log_group).add("tri.resource.class", "application")
        ######################### PARAMETERS #################
        # We now have everything we need to generate the appropriate parameters
        self.parameters.generate_service_parameters_and_secrets()

        # We create the adot configuration for the stack
        # TODO: Replace the workspace_id with a configuration-based parameter
        self.adot_configuration = ADOTConfiguration(self, "adot_configuration",
            workspace_id="ws-5ee14a48-7d8a-4d34-8c3f-f9ba6a41d97b",
            region=self.region,
            account=self.account,
            base_parameter_path=self.parameters.parameter_base_path
        )

        ########################## ECS CLUSTER #################
        # 1 AWS Fargate Service in Private Subnet
        self.cluster = ecs.Cluster(self, base_id + "-cluster", vpc=self.networking.vpc)
        Tags.of(self.cluster).add("tri.resource.class", "application")

        # We generate the services dynamically
        self.services : dict[str, FargateService] = { }

        for service in self.parameters.service_parameters:
            self.services[service] = FargateService(self, base_id + "-" + service + "Service",
                app_name=self.parameters.app_name,
                cluster=self.cluster,
                service_params=self.parameters.service_parameters[service],
            )
            self.services[service].addOtel(self.adot_configuration)

            # We ask the efs storage to attach itself to the service if necessary
            self.storage.attach_storage_to_service(self.services[service])

            # We add the service to the target group
            self.networking.add_fargate_target_group("ECS-" + service, self.services[service])