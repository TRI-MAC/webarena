from typing import Optional
from constructs import Construct

from aws_cdk import (
    CfnDeletionPolicy,
    aws_ec2 as ec2,
    aws_iam as iam,
    Tags,
)

from .configuration.configuration import EC2InstanceParams

# CloudWatch agent config template — CW_LOG_GROUP_PREFIX is replaced at construct time;
# {instance_id} is a CloudWatch agent runtime variable, not a Python format placeholder.
_CW_AGENT_CONFIG_TEMPLATE = """{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/webarena-startup.log",
            "log_group_name": "CW_LOG_GROUP_PREFIX/startup",
            "log_stream_name": "{instance_id}",
            "timestamp_format": "%Y-%m-%dT%H:%M:%S"
          },
          {
            "file_path": "/var/log/shopping.log",
            "log_group_name": "CW_LOG_GROUP_PREFIX/shopping",
            "log_stream_name": "{instance_id}"
          },
          {
            "file_path": "/var/log/shopping_admin.log",
            "log_group_name": "CW_LOG_GROUP_PREFIX/shopping_admin",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  }
}"""


class WebArenaEC2(Construct):
    """
    WebArena EC2 Construct

    Deploys a single EC2 instance from the WebArena AMI with:
    - IAM role granting CloudWatch agent and SSM access
    - Security group allowing open_ports from anywhere
    - EBS root volume (gp3, configurable size)
    - Optional SSH key pair
    - User data that:
        1. Installs and configures the CloudWatch agent to stream logs
        2. Starts the shopping/shopping_admin Docker containers
        3. Configures Magento base URLs using the instance's private IP
           (queried from the EC2 metadata service at boot time)
        4. Streams Docker logs and Magento exception logs to CloudWatch

    Attributes:
        instance : ec2.Instance
        security_group : ec2.SecurityGroup
        role : iam.Role
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        vpc: ec2.IVpc,
        ami_id: str,
        params: EC2InstanceParams,
        log_group_prefix: str = "/webarena",
        zone_name: str = "webarena.dev.hcai.tri.global",
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        # IAM role — CloudWatch agent + SSM (SSM enables in-VPC shell access without SSH)
        self.role = iam.Role(
            self,
            "InstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "CloudWatchAgentServerPolicy"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSSMManagedInstanceCore"
                ),
            ],
        )

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

        cw_config = _CW_AGENT_CONFIG_TEMPLATE.replace(
            "CW_LOG_GROUP_PREFIX", log_group_prefix
        )

        # User data: install CW agent, start containers, configure Magento base URLs
        user_data = ec2.UserData.for_linux()

        user_data.add_commands(
            # Redirect all output to startup log from the very beginning
            "exec > >(tee /var/log/webarena-startup.log) 2>&1",
            "",
            "# --- CloudWatch agent setup (best-effort, runs before set -e) ---",
            "if ! [ -f /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl ]; then",
            "  if command -v yum &>/dev/null; then",
            "    yum install -y amazon-cloudwatch-agent || true",
            "  else",
            "    cd /tmp",
            "    wget -q https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb",
            "    dpkg -i -E ./amazon-cloudwatch-agent.deb || true",
            "  fi",
            "fi",
            "",
            "mkdir -p /opt/aws/amazon-cloudwatch-agent/etc",
            # Write CW agent config via heredoc (single command with embedded newlines)
            "cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'CWEOF'\n"
            + cw_config
            + "\nCWEOF",
            "",
            "# Start CW agent — from this point stdout/stderr stream to CloudWatch",
            "/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl"
            " -a fetch-config -m ec2"
            " -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json"
            " -s || true",
            "",
            "set -e",
            "",
            "# === Persistent data volume ===",
            "# Stop Docker before moving its data directory to the persistent EBS.",
            "systemctl stop docker 2>/dev/null || true",
            "",
            "# Wait for the data volume to attach (CloudFormation attaches it after",
            "# instance creation; the loop allows up to 2 min for the attachment).",
            "for _i in $(seq 1 60); do",
            "  # On NVMe-based instances /dev/xvdf appears as nvme1n1 (nvme0n1 is root).",
            "  DATA_DEV=$(lsblk -d -n -o NAME | grep -E '^nvme[1-9]n[0-9]+' | head -1)",
            "  [ -z \"$DATA_DEV\" ] && DATA_DEV=$(test -b /dev/xvdf && echo xvdf || true)",
            "  [ -n \"$DATA_DEV\" ] && break",
            "  sleep 2",
            "done",
            "[ -z \"$DATA_DEV\" ] && { echo 'ERROR: data volume not found'; exit 1; }",
            "DATA_DEV=\"/dev/${DATA_DEV}\"",
            "echo \"Data volume device: $DATA_DEV\"",
            "",
            "if ! blkid \"$DATA_DEV\" &>/dev/null; then",
            "  echo 'New volume — formatting and migrating Docker data (first boot)...'",
            "  mkfs.ext4 -F \"$DATA_DEV\"",
            "  mkdir -p /mnt/docker-data",
            "  mount \"$DATA_DEV\" /mnt/docker-data",
            "  rsync -axX /var/lib/docker/ /mnt/docker-data/",
            "  umount /mnt/docker-data",
            "fi",
            "",
            "mount \"$DATA_DEV\" /var/lib/docker",
            "echo \"$DATA_DEV /var/lib/docker ext4 defaults,nofail 0 2\" >> /etc/fstab",
            "echo 'Persistent data volume mounted at /var/lib/docker'",
            "",
            "# Start Docker on the persistent volume",
            "systemctl start docker",
            "",
            "# Brief pause for Docker to finish starting",
            "sleep 10",
            "",
            "# Start WebArena containers and ensure they restart on reboot",
            "docker update --restart=always shopping shopping_admin",
            "docker start shopping",
            "docker start shopping_admin",
            "",
            "# Stream Docker logs to files so CW agent can pick them up",
            "nohup docker logs -f shopping  >> /var/log/shopping.log       2>&1 &",
            "nohup docker logs -f shopping_admin >> /var/log/shopping_admin.log 2>&1 &",
            "",
            "# Get private IP from instance metadata service (IMDSv2)",
            'IMDS_TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")',
            'PRIVATE_IP=$(curl -s -H "X-aws-ec2-metadata-token: $IMDS_TOKEN" http://169.254.169.254/latest/meta-data/local-ipv4)',
            "",
            "# Wait for Magento to initialize",
            "sleep 120",
            "",
            "# Configure shopping (port 7770)",
            'docker exec shopping /var/www/magento2/bin/magento setup:store-config:set --base-url="http://${PRIVATE_IP}:7770"',
            # Use double quotes so bash expands ${PRIVATE_IP}; single quotes inside for SQL values
            "docker exec shopping mysql -u magentouser -pMyPassword magentodb -e"
            " \"UPDATE core_config_data SET value='http://${PRIVATE_IP}:7770/' WHERE path = 'web/secure/base_url';\"",
            "docker exec shopping /var/www/magento2/bin/magento cache:flush",
            "",
            "# Configure shopping_admin (port 7780)",
            'docker exec shopping_admin /var/www/magento2/bin/magento setup:store-config:set --base-url="http://${PRIVATE_IP}:7780"',
            "docker exec shopping_admin mysql -u magentouser -pMyPassword magentodb -e"
            " \"UPDATE core_config_data SET value='http://${PRIVATE_IP}:7780/' WHERE path = 'web/secure/base_url';\"",
            "docker exec shopping_admin php /var/www/magento2/bin/magento config:set admin/security/password_is_forced 0",
            "docker exec shopping_admin php /var/www/magento2/bin/magento config:set admin/security/password_lifetime 0",
            "docker exec shopping_admin /var/www/magento2/bin/magento cache:flush",
            "",
            "# Dump Magento exception + system logs into the shopping log files",
            "echo '=== shopping exception.log ==='",
            "docker exec shopping cat /var/www/magento2/var/log/exception.log 2>/dev/null || true",
            "echo '=== shopping system.log ==='",
            "docker exec shopping cat /var/www/magento2/var/log/system.log 2>/dev/null || true",
            "echo '=== shopping_admin exception.log ==='",
            "docker exec shopping_admin cat /var/www/magento2/var/log/exception.log 2>/dev/null || true",
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
            role=self.role,
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

        # Persistent data volume — survives instance replacement and stack deletion.
        # All Docker data (container writeable layers, named volumes, MySQL) lives here.
        self.data_volume = ec2.CfnVolume(
            self,
            "DataVolume",
            availability_zone=self.instance.instance_availability_zone,
            size=500,
            volume_type="gp3",
            encrypted=True,
        )
        self.data_volume.cfn_options.deletion_policy = CfnDeletionPolicy.RETAIN
        self.data_volume.cfn_options.update_replace_policy = CfnDeletionPolicy.RETAIN

        ec2.CfnVolumeAttachment(
            self,
            "DataVolumeAttachment",
            instance_id=self.instance.instance_id,
            volume_id=self.data_volume.ref,
            device="/dev/xvdf",
        )

        # The org SCP blocks ec2:DeleteTags for the CFN execution role.
        # Overriding Tags with add_override (which runs after CDK's TagManager)
        # freezes the instance's tag set to exactly what was in the last
        # successfully deployed template. This prevents any DeleteTags call,
        # keeping the EC2 resource a no-op in every changeset.
        # To update instance tags, use aws ec2 create-tags out-of-band.
        cfn_instance = self.instance.node.default_child
        cfn_instance.add_override("Properties.Tags", [
            {"Key": "Name", "Value": "webarena-development/webarena-development-EC2/Instance"},
            {"Key": "app-name", "Value": "webarena"},
            {"Key": "environment", "Value": "development"},
            {"Key": "hcai.projectname", "Value": "REPLACE_WITH_PROJECT_NAME"},
            {"Key": "hcai.stakeholder.email", "Value": "REPLACE_WITH_EMAIL"},
            {"Key": "tri.owner", "Value": "REPLACE_WITH_OWNER"},
            {"Key": "tri.owner.email", "Value": "REPLACE_WITH_EMAIL"},
            {"Key": "tri.project", "Value": "REPLACE_WITH_PROJECT_CODE"},
            {"Key": "tri.resource.class", "Value": "application"},
        ])
