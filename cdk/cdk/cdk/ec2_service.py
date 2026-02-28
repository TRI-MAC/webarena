from typing import Optional
from constructs import Construct

from aws_cdk import (
    aws_ec2 as ec2,
    Tags,
)

from .configuration.configuration import EC2InstanceParams


class WebArenaEC2(Construct):
    """
    WebArena EC2 Construct

    Deploys a single EC2 instance from the WebArena AMI with:
    - Security group allowing open_ports from anywhere
    - EBS root volume (gp3, configurable size)
    - Optional SSH key pair
    - User data that starts the shopping/shopping_admin Docker containers
      and configures Magento base URLs using the instance's public IP
      (queried from the EC2 metadata service at boot time)

    Attributes:
        instance : ec2.Instance
        security_group : ec2.SecurityGroup
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        vpc: ec2.IVpc,
        ami_id: str,
        params: EC2InstanceParams,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        # Security group
        self.security_group = ec2.SecurityGroup(
            self,
            "SG",
            vpc=vpc,
            description="WebArena EC2 security group",
            allow_all_outbound=True,
        )
        for port in params.open_ports:
            self.security_group.add_ingress_rule(
                peer=ec2.Peer.any_ipv4(),
                connection=ec2.Port.tcp(port),
                description=f"Allow TCP {port}",
            )

        # User data: start containers, wait, then configure Magento base URLs
        user_data = ec2.UserData.for_linux()

        user_data.add_commands(
            "set -e",
            "exec > >(tee /var/log/webarena-startup.log) 2>&1",
            "",
            "# Wait for Docker daemon",
            "sleep 30",
            "",
            "# Start WebArena containers",
            "docker start shopping",
            "docker start shopping_admin",
            "",
            "# Get private IP from instance metadata service",
            "PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/local-ipv4)",
            "",
            "# Wait for Magento to initialize",
            "sleep 120",
            "",
            "# Configure shopping (port 7770)",
            'docker exec shopping /var/www/magento2/bin/magento setup:store-config:set --base-url="http://${PUBLIC_IP}:7770"',
            "docker exec shopping mysql -u magentouser -pMyPassword magentodb -e"
            " 'UPDATE core_config_data SET value=\"http://${PUBLIC_IP}:7770/\" WHERE path = \"web/secure/base_url\";'",
            "docker exec shopping /var/www/magento2/bin/magento cache:flush",
            "",
            "# Configure shopping_admin (port 7780)",
            'docker exec shopping_admin /var/www/magento2/bin/magento setup:store-config:set --base-url="http://${PUBLIC_IP}:7780"',
            "docker exec shopping_admin mysql -u magentouser -pMyPassword magentodb -e"
            " 'UPDATE core_config_data SET value=\"http://${PUBLIC_IP}:7780/\" WHERE path = \"web/secure/base_url\";'",
            "docker exec shopping_admin php /var/www/magento2/bin/magento config:set admin/security/password_is_forced 0",
            "docker exec shopping_admin php /var/www/magento2/bin/magento config:set admin/security/password_lifetime 0",
            "docker exec shopping_admin /var/www/magento2/bin/magento cache:flush",
            "",
            "echo 'WebArena startup complete'",
        )

        # EC2 instance
        instance_type = ec2.InstanceType(params.instance_type)
        machine_image = ec2.MachineImage.generic_linux({"us-east-1": ami_id})

        instance_kwargs = dict(
            instance_type=instance_type,
            machine_image=machine_image,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_group=self.security_group,
            user_data=user_data,
            block_devices=[
                ec2.BlockDevice(
                    device_name="/dev/sda1",
                    volume=ec2.BlockDeviceVolume.ebs(
                        params.volume_size_gib,
                        volume_type=ec2.EbsDeviceVolumeType.GP3,
                        delete_on_termination=True,
                    ),
                )
            ],
        )

        if params.key_pair_name:
            instance_kwargs["key_pair"] = ec2.KeyPair.from_key_pair_name(
                self, "KeyPair", params.key_pair_name
            )

        self.instance = ec2.Instance(self, "Instance", **instance_kwargs)

        Tags.of(self).add("tri.resource.class", "application")
