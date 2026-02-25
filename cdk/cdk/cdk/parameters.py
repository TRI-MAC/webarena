from constructs import Construct

# CDK imports
from aws_cdk import (
    aws_secretsmanager as secretsmanager,
    aws_ssm as ssm,
    aws_ecs as ecs,
    aws_logs as logs,
)
from dataclasses import asdict
from .configuration.configuration import (
    load_configuration
)

from .storage import (
    StorageParameters,
    Storage
)

from .networking import (
    NetworkingParameters,
    Networking
)

from .fargate_service import (
    FargateServiceParameters
)

from .cognito import (
    CognitoParameters
)

from .utils import (
    sanitize_name,
    generate_parameter_hashes_from_object
)

class Parameters(Construct):
    """
    Parameters Construct

    The parameters construct is responsible for parsing the configuration file and preparing the necessary parameter structures for the constructs to be deployed.
    The parameters construct is also responsible for creating the various systems manager secrets and parameters necessary for the ecs application to run.

    Attributes:
        parameter_base_path : str
            The base path for the created parameters
        vpcid : str | None
            The id of the vpc in which to create the various resources
        app_name : str
            The name of the application (this is also the stack name)
        deploy_env : str
            The deployment environment used
        cert_arn : str | None
            The ARN of the SSL Certificate
        storage_parameters : StorageParameters
            The parameters necessary to deploy the Storage Construct
        networking_parameters : NetworkingParameters
            The parameters necessary to deploy the Networking Construct

        services_parameters:
            The parameters for frontend and backend services
        frontend_parameters:
            The environment variables for the frontend service
        backend_parameters:
            The environment variables for the backend service
        aws_services_parameters:
            The parameters for aws services

        frontend_secrets:
            The frontend secrets
        backend_secrets
            The backend secrets

        uuid: str
            Stable uuid for the stack which can be used to create unique names for storage, etc...

    """
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        """
        Creates the Parameter Construct

        Create the parameter construct which manages the variables and configurations required for the rest of the stack.

        Parameters:
        - scope : Construct
        - id : str
            The base id for the construct
        """
        super().__init__(scope, id, **kwargs)

        # First load the information from context
        self.deploy_env = self.node.try_get_context("deploy_env")
        if not self.deploy_env:
            # We use development as our base if we don't find a deploy_env
            self.deploy_env = "development"

        # We get the image tag from context, if we don't find it we assume we want the latest image_tag and we set the context:
        image_tag = self.node.try_get_context("image_tag")
        if not image_tag:
            image_tag = "latest"


        # Load the config file
        self.__conf = load_configuration("../config/{0}.yaml".format(self.deploy_env))
        
        #Lowercasing and removing any non-hyphen symbols
        self.app_name = sanitize_name(self.__conf.app_name)
        self.parameter_base_path = "/" + self.app_name + "/" + self.deploy_env + "/"

        # We set specific parameters that we access frequently
        self.vpcid = self.__conf.aws.vpcid
        self.cert_arn = self.__conf.aws.cert


        # Storage parameters are setup from config
        self.storage_parameters = StorageParameters(
            s3=self.__conf.aws_services.s3,
            dynamodb=self.__conf.aws_services.dynamodb,
            efs=self.__conf.aws_services.efs,
            aurora=self.__conf.aws_services.aurora,
            elasticache=self.__conf.aws_services.elasticache
        )
    
        # Networking parameters are setup from config
        self.networking_parameters = NetworkingParameters(
            vpcid=self.__conf.aws.vpcid,
            cert_arn=self.__conf.aws.cert,
            subnet_ids=self.__conf.aws.subnet_ids,
        )

        # We create the empty cognito parameters, these will be filled up from the network construct after
        self.cognito_parameters = CognitoParameters(**self.__conf.aws_services.amplify)

        # For each of our services in the config file, we add a fargate service parameters
        self.service_parameters : dict[str, FargateServiceParameters] = {}
        for service in self.__conf.app_services:
            # We use the service name (key) as the identifier
            self.service_parameters[service] = FargateServiceParameters(**asdict(self.__conf.app_services[service]),
                image_tag=image_tag,
                identifier=service,
                app_name=self.app_name,
                environment=self.deploy_env
            )

        # # Our frontend service parameters are definded from the config
        # self.front_end_service_parameters = FargateServiceParameters(**self.__conf.frontend, image_tag=image_tag)

        # # Our backend service parameters are definded from the config
        # self.back_end_service_parameters = FargateServiceParameters(**self.__conf.backend, image_tag=image_tag)
        # print(self.service_parameters)

    ### SETTERS
    def set_storage_params(self, storage_construct : Storage) -> None:
        """
        Set Storage Parameters

        Sets the parameters defined by the storage construct.
        That is the name (from cloud formation) for the databucket and dynamodb table.
        This is later used to inject into environment variables

        Parameters:
            data_bucket_resolved_name : str
                The resolved name of the databucket which can be used to connect / store information on it
            dynamodb_table_name : str
                The name of the dynamodb table that was created by cdk (and that should be used by the applications)
        """
        if storage_construct.data_bucket:
            self.__conf.aws_services.s3.data_bucket_resolved_name = storage_construct.data_bucket.bucket_name
        
        if storage_construct.dynamodb_table:
            self.__conf.aws_services.dynamodb.table_name = storage_construct.dynamodb_table.table_name

        if storage_construct.aurora_storage:
            self.__conf.aws_services.aurora.cluster_endpoint = storage_construct.aurora_storage.cluster.cluster_endpoint.hostname
            self.__conf.aws_services.aurora.cluster_port = storage_construct.aurora_storage.cluster.cluster_endpoint.port
            self.__conf.aws_services.aurora.cluster_user = "admin"

        if storage_construct.elasticache_storage:
            self.__conf.aws_services.elasticache.cache_endpoint = storage_construct.elasticache_storage.cache.attr_primary_end_point_address

    def set_networking_parameters(self, networking_construct : Networking) -> None:
        """
        Set Networking Parameters

        Sets the values of various properties from the networking construct

        Parameters:
            networking_construct : Networking
                The deployed networking construct
        """
        # We set the properties in self.__conf based on the new lb_url
        # self.__conf.frontend.service_url = networking_construct.lb_url
        # self.__conf.backend.service_url = networking_construct.lb_url
        for service in self.__conf.app_services:
            self.__conf.app_services[service].service_url = networking_construct.lb_url

        # We also modify the proper cognito params
        self.cognito_parameters.callback_urls.append(networking_construct.lb_url)
        self.cognito_parameters.cert = networking_construct.cert

    def set_user_pool_information(self, user_pool_id : str, user_pool_client_id : str) -> None:
        """
        Setup user pool information

        Sets the values for the user pool which will be injected into the services

        Parameters:
            user_pool_id : str
                The ID of the Cognito user pool
            user_pool_client_id : str
                The ID of the Client ID for AWS Amplify
        """
        self.__conf.aws_services.amplify.auth.user_pool_id = user_pool_id
        self.__conf.aws_services.amplify.auth.web_client_id = user_pool_client_id


    def set_log_group(self, log_group : logs.LogGroup) -> None:
        """
        Set the log group

        When the log group is created, sets the log group for the various services that need it
        """

        self.back_end_service_parameters.log_group = log_group
        self.front_end_service_parameters.log_group = log_group

    def set_uuid(self, uuid: str) -> None:
        """
        Set Stable UUID

        Sets a stable uuid which can be used to deploy uniquely named values in the stack (ex: buckets, dynamodb tables, etc...)
        """
        self.uuid = uuid

    ### CREATE PARAMETER HASH FUNCTIONS
    def __create_parameter(self, key_string : str, value : str):
        """
        Create Parameter

        Creates the parameter in SSM and returns the parameter as a secret
        """
        cur_parameter = ssm.StringParameter(self, key_string,
            parameter_name = self.parameter_base_path + key_string,
            string_value = value
        )
        return ecs.Secret.from_ssm_parameter(cur_parameter)
    
    
    # This method combines multiple hashes together to form a larger hash
    def __combine_hashes(self, hashes : list[dict]) -> dict:
        """
        Combines a list of dictionaries

        This method takes a list of dictionaries and returns a dictionary that is a combination of these input dictionaries.

        Parameters:
        - hashes : list[dict]
            the dictionaries to combine
        
        Returns:
        - dict : the combined dictionary
        """
        # If we have an empty list, we return an empty hash
        if hashes.count == 0:
            return {}
        # If we have only 1 hash, we return the first hash
        if hashes.count == 1:
            return hashes[0]
        

        # Otherwise we go through each hash and copy / add it to the first hash
        returned_hash = {}
        for i in range(len(hashes)):
            if i == 0:
                returned_hash = hashes[i].copy()
            else:
                returned_hash.update(hashes[i])

        return returned_hash
    
    def __create_secret_names_from_keys(self, base_keys : list[str], base_dictionary : dict) -> dict:
        """
        Create secret names from keys

        This method generates the secret in secret manager for the keys specified in the configuration file.
        When the secrets have been created, their values should be set on AWS itself. This is for security of the secrets.

        Parameters:
        - base_keys : list[str]
            List of base keys found in the configuration file which contain the names of the secrets to generate
        - base_dictionary : dict
            The dictionary which contains the secret keys
        Returns:
        - dict : hash of the secret keys generated 
        """
        returned_secret_hash = {}
        
        for base_key in base_keys:
            if base_key in base_dictionary:
                # Secrets are single-key elements
                # secret_names = base_dictionary[base_key]
                # if secret_names:
                #     print(secret_names)
                for secret in base_dictionary[base_key]:
                    cur_secret = secretsmanager.Secret(self, base_key + "-" + secret + "-secret",
                        secret_name=self.parameter_base_path + secret
                    )

                    cur_ecs_secret = ecs.Secret.from_secrets_manager(cur_secret)
                    
                    returned_secret_hash[secret] = cur_ecs_secret
                    
        return returned_secret_hash
    

    def generate_service_parameters_and_secrets(self) -> None:
        """
        Generate Service Parameters and Secrets

        This method generates the service parameters and secrets based on the configuration file (and modification made by generating resources such as LB, etc...)

        Creates the following attributes:
        - self.front_end_service_parameters.secrets
        - self.back_end_service_parameters.secrets
        
        """
        # Any parameter stored in the config files are considere to be non-sensitive so we will store them in ParameterStore.
        # For sensitive information that should be used inside the application (API Keys, etc...), we recommend using Secrets Manager
        # These should then be retrieved using the proper aws libraries


        # Populate / Update the parameters for the services file
        services_parameters = generate_parameter_hashes_from_object(
            input_object=asdict(self.__conf),
            base_keys=["app_services", "app_url"],
            param_creation_method=self.__create_parameter
        )

        aws_services_parameters = generate_parameter_hashes_from_object(
            input_object=asdict(self.__conf.aws_services),
            base_keys=[key for key in asdict(self.__conf.aws_services)],
            separate_hashes=True,
            key_prefix="aws_services",
            param_creation_method=self.__create_parameter
        )

        # We generate all the environment variables needed to run the individual services
        services_environments = generate_parameter_hashes_from_object(
            input_object=self.__conf.app_environments,
            base_keys=[key for key in self.__conf.app_services],
            param_creation_method=self.__create_parameter,
            separate_hashes=True
        )
    
        ########################## SECRETS ##########################
        # We get the secret names from the config file
        services_secrets = {}
        for service in self.__conf.app_services:
            services_secrets[service] = self.__create_secret_names_from_keys(
                [service],
                self.__conf.app_secrets
            )

        system_secrets = self.__create_secret_names_from_keys(
            ["system_wide"],
            self.__conf.app_secrets
        )

        ### Finally, we combine the hashes to make them work for the all app services systems
        for service in self.__conf.app_services:
            # Each service is allowed to access:
            # - service_parameters
            # - service_environments for that service
            # - service_secrets for that service
            # - aws_services_parameters for the services they utilized
            hashes_to_combine = [
                services_parameters,
                system_secrets
            ]
            if service in services_environments:
                hashes_to_combine.append(services_environments[service])

            if service in services_secrets:
                hashes_to_combine.append(services_secrets[service])
            
            for aws_service in asdict(self.__conf.app_services[service].enabled_service_connections):
                hashes_to_combine.append(aws_services_parameters[aws_service])

            self.service_parameters[service].secrets = self.__combine_hashes(
                hashes_to_combine
            )
