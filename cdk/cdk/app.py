#!/usr/bin/env python3
# Other imports
import os

from cdk.utils import (
    sanitize_name
)

from cdk.configuration.configuration import (
    load_configuration
)

from aspects.TRIChecker import (
    TRIChecker
)
# import argparse

# CDK imports
import aws_cdk as cdk
from cdk.cdk_stack import CdkStack


app = cdk.App()
# Load environment from file using the context for deploy_env and image_tag
# To use these use --context deploy_env={value} --context image_tag={value}
# or
# -c deploy_env={value} -c image_tag={value}

deploy_env = app.node.try_get_context("deploy_env")
if not deploy_env:
    print("defaulting to development")
    deploy_env = "development"
    app.node.set_context("deploy_env", deploy_env)
    
image_tag = app.node.try_get_context("image_tag")
if not image_tag:
    print("defaulting to latest")
    image_tag = "latest"
    app.node.set_context("image_tag", image_tag)



print("CDK Stack for the environment: " + deploy_env + "with image tag" + image_tag)
conf = load_configuration("../config/{0}.yaml".format(deploy_env))

#Ensures the stack name meets requirements for AWS for symbols, length, and lowercase
sanitized_stack_name = sanitize_name(conf.app_name)

# We add our CdkStack in the app
CdkStack(app, sanitized_stack_name + "-" + deploy_env,
    # If you don't specify 'env', this stack will be environment-agnostic.
    # Account/Region-dependent features and context lookups will not work,
    # but a single synthesized template can be deployed anywhere.

    # Uncomment the next line to specialize this stack for the AWS Account
    # and Region that are implied by the current CLI configuration.

    # env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),

    # Uncomment the next line if you know exactly what Account and Region you
    # want to deploy the stack to. */
    env=cdk.Environment(account=conf.aws.account, region=conf.aws.region),
    # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
)

cdk.Tags.of(app).add("app-name", sanitized_stack_name);
cdk.Tags.of(app).add("environment", conf.env);

for tag in conf.tags:
    cdk.Tags.of(app).add(tag,conf.tags[tag])

TRIChecker(app)

app.synth()
