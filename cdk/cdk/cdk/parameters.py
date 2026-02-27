from constructs import Construct

from .configuration.configuration import (
    load_configuration,
    EC2InstanceParams,
)

from .networking import NetworkingParameters

from .utils import sanitize_name


class Parameters(Construct):
    """
    Parameters Construct

    Parses the configuration file and prepares parameter structures for the stack.

    Attributes:
        app_name : str
        deploy_env : str
        ami_id : str
            AMI ID passed via CDK context (-c ami_id=...)
        vpcid : str
        networking_parameters : NetworkingParameters
        ec2_instance : EC2InstanceParams
        tags : dict[str, str]
    """

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.deploy_env = self.node.try_get_context("deploy_env") or "development"

        self.__conf = load_configuration("../config/{0}.yaml".format(self.deploy_env))

        self.app_name = sanitize_name(self.__conf.app_name)
        self.vpcid = self.__conf.aws.vpcid
        self.tags = self.__conf.tags

        self.networking_parameters = NetworkingParameters(vpcid=self.__conf.aws.vpcid)
        self.ec2_instance = self.__conf.ec2_instance
