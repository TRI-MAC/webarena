import string
from typing import Optional
from constructs import Construct

from aws_cdk import (
    # Duration,
    aws_ssm as ssm
)

# ADOT CONFIGURATION For use with the sidecar in ECS
class ADOTConfiguration(Construct):

  def __init__(self, scope: Construct, id: str,
      workspace_id : string,
      region : string,
      account: string,
      base_parameter_path : string = "",
      **kwargs
  ) -> None:

    super().__init__(scope, id, **kwargs)
    self.region = region
    self.account = account
    self.workspace_id = workspace_id
    self.remote_write_url = "https://aps-workspaces." + self.region + ".amazonaws.com/workspaces/" + self.workspace_id + "/api/v1/remote_write"

    adot_config_content = f"""
      receivers:
        otlp:
          protocols:
            grpc:
            http:
        prometheus:
          config:
            global:
              scrape_interval: 15s
              scrape_timeout: 10s
            scrape_configs:
            - job_name: "prometheus"
              static_configs:
              - targets: [ 0.0.0.0:9090 ]
        awsecscontainermetrics:
          collection_interval: 10s
      processors:
        batch:
        resourcedetection:
          detectors: [env, ecs]
      exporters:
        prometheusremotewrite:
          endpoint: {self.remote_write_url}
          auth:
            authenticator: sigv4auth
        debug:
          verbosity: detailed
        awsxray:
      extensions:
        health_check:
        pprof:
          endpoint: :1888
        zpages:
          endpoint: :55679
        sigv4auth:
          region: {self.region}

      service:
        extensions: [pprof, zpages, health_check, sigv4auth]
        pipelines:
          traces:
            receivers: [otlp]
            processors: [batch]
            exporters: [awsxray]
          metrics:
            receivers: [otlp, prometheus]
            processors: [batch, resourcedetection]
            exporters: [debug, prometheusremotewrite]
          metrics/ecs:
            receivers: [awsecscontainermetrics]
            exporters: [debug, prometheusremotewrite]
      """
    
    # We create an ssm string parameter with the prometheus configuration
    self.adot_config_parameter = ssm.StringParameter(self, "AdotConfigParam",
      parameter_name=base_parameter_path + "adot/ecs/prometheus-config",
      string_value=adot_config_content
    )