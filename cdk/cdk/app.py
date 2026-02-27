#!/usr/bin/env python3
import os

from cdk.utils import sanitize_name
from cdk.configuration.configuration import load_configuration
from aspects.TRIChecker import TRIChecker

import aws_cdk as cdk
from cdk.cdk_stack import CdkStack


app = cdk.App()

deploy_env = app.node.try_get_context("deploy_env")
if not deploy_env:
    print("defaulting to development")
    deploy_env = "development"
    app.node.set_context("deploy_env", deploy_env)

print("CDK Stack for the environment: " + deploy_env)
conf = load_configuration("../config/{0}.yaml".format(deploy_env))

sanitized_stack_name = sanitize_name(conf.app_name)

CdkStack(app, sanitized_stack_name + "-" + deploy_env,
    env=cdk.Environment(account=conf.aws.account, region=conf.aws.region),
)

cdk.Tags.of(app).add("app-name", sanitized_stack_name)
cdk.Tags.of(app).add("environment", conf.env)

for tag in conf.tags:
    cdk.Tags.of(app).add(tag, conf.tags[tag])

TRIChecker(app)

app.synth()
