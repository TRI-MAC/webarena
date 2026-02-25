# CDK Web App Template Repository

## Repository Purpose

This is your space, please add any information related to the frontend and backend services, what they do, etc...

## Template Purpose
The purpose of this document is to provide a basic overview of the serverless template. More information can be found in this README.md and the other README.md files across the template.

For a user guide on how to use this template, click the link to view the user guide on Confluence: [Web-App-Template User Guide](https://toyotaresearchinstitute.atlassian.net/l/cp/Q3CmtCd1)

## How to create a new repository based on a template
To view instructions on how to create a new repository based on a template, "Create from template" section on the Confluence page: [Create/Upgrade from Template](https://toyotaresearchinstitute.atlassian.net/l/cp/98eQEGYd)

## How to update a repository to a newer version of the template

To view instructions on how to update a repository based on an updated version of the template, view the "Upgrade from template" section on the link to view the Confluence page: [Create/Upgrade from Template](https://toyotaresearchinstitute.atlassian.net/l/cp/98eQEGYd)

## CLONING INTO WSL2
In order for the repository to work on Windows with WSL2 please follow these instructions:
- Open WSL from the windows terminal
- navigate to the home path
- Open VSCode using the termina (code .)
- Clone from the opened WSL-based VSCode
- From there using DevContainers should work as expected

## Repository Structure

### Application Code

#### Backend

The [backend folder](backend) is where the backend (api) code for the application is found. The default sample backend application is a FastAPI backend.

It includes a Dockerfile which is used to build the backend code into a docker container to be run either locally or on the cloud.

This directory also contains docker-compose and docker-compose.dev files which instruct the main docker-compose files how to run the backend in the context of a local development or local production run.


##### Selecting other backend framework 
To ensure that the necessary docker files remain please merge or overwrite the folders.


#### Frontend

The [frontend folder](frontend) is where the frontend of the application (ui) code for the application is found. The sample application is a Next.JS application using NextJs Router.

For more information on setting up the FrontEnd using NextJS or converting an existing create-react-app to NextJS, please see the [README.md](frontend/README.md) file in the frontend directory.

Similarly to the backend, this directory also contains docker-compose and docker-compose.dev files which instruct the main compose files how to run the frontend.

### CDK
The CDK folder contains all the AWS CDK code for IaC. It deploys the necessary infrastructure to run the FrontEnd and backend services and access them through an Applcation Load Balancer.

For more information on the deployed infrastructure, please see the [README.md](cdk/README.md) file in the CDK directory.


### Configuration
The configuration folder contains yaml files that represent the various configuration options for any given environment.

The [local.yaml](config/local.yaml) file contains the configuration for local development

The [development.yaml](config/development.yaml) file contains the configuration for the development environment


### Sample Services
The sample services directory contains sample starters for various languages that can be used for both the frontend and backend.

This enables an easy way of switching / starting a new project with a working backend which includes the proper Dockerfiles, docker-compose files etc...


### Scripts
The scripts folder contains utility scripts used including to run the application locally and to run unit tests for the infrastructure code.


## Local Deployment / Development

### Configuration
All required configurations should go in the [local environment yaml file](config/local.yaml) found in the config directory.


### Running Locally

When you are satisfied with your configuration please run the [scripts/run_local.sh](scripts/run_local.sh) from the root of the repository:

```bash
bash scripts/run_local.sh
```

Internally, this will activate the proper python environment, create the proper environment files and run docker-compose.

Docker compose will take charge of building the environments and setting up the proper environment variables (as generated above).

Before running the services, please make sure to have aws credentials properly set if you need to access aws services from within the backend service.

Both the frontend and backend can now be accessed using http://cdkweb-app-template.localhost using Traefik. **NOTE: this only affects local run**

**NOTE** Please make sure to add the following to your host file

```
127.0.0.1   cdk-web-app-template.localhost
127.0.0.1   api.cdk-web-app-template.localhost
```

For re-purposing existing applications to run locally using traefik, please look at the docker-compose.dev and docker-compose.dev.yaml files as the appropriate networking and docker-compose labels have been setup.


When you are finished running locally, please run the cleanup script:

```bash
bash scripts/cleanup_local_run.sh
```

Note: This will remove docker networks, running containers and any other resources. If there is data storage involved, please make sure to have a backup.

**NOTE: In order to use ecs-local-endpoints please create an aws profile using the following command: aws configure sso (leave the name of the sso session blank for this to work with ecs-local-endpoints)**
Issue: https://github.com/awslabs/amazon-ecs-local-container-endpoints/issues/278

## Cloud Deployment

The repository is setup to utilize Github Actions to automate the deployment of the web app.

### Configuration
Create a configuration yaml file for the environment that you want to deploy.
See "development.yaml" for reference

If you have a Route53 URl, please utilize it.

### Automated Build and Deploy Process
Whenever a commit is created on the main branch, the development deployment workflow is triggered.
This workflow has 2 steps:
- Step 1: Build Docker images
- Step 2: Run CDK Deploy

Both of these steps use the development.yaml file for configurations so make sure that it is properly setup.

### Notes
After the initial deployment, you may need to update the configuration file to add information such as the resolved bucket names and service urls as they are generated during the initial deployment.

If the frontend or backend services require secrets, you should add the values to the secrets created by CDK.


## Template and Application Versioning

### Introduction

The template repository (and any derived web application) has been setup to create version tags automatically upon new commits being made to the master branch, or when a development deploy is triggered manually.

The methodology behind version tagging is [Semantic Versioning](https://gitversion.net/docs/learn/intro-to-semver). That is version take the form of `major.minor.patch` which allows stable builds to be created and easy reference to specific builds by version number.

The system used by the repository is [https://gitversion.net/](https://gitversion.net/)

Major versions will introduce breaking features (breaks compatibility with other APIs, data structures, etc...)

Minor versions are introduction of non-breaking features.

Patch versions are for bug fixes.



### Incrementing Version using commits
While the system automatically increments patch commits by default, minor and major versions must be declared in commit messages.

Adding the following will increment the major, minor or patch version: 

- Major Version: `+semver: major` or `+semver: breaking`
- Minor Version: `+semver: minor` or `+semver: feature`
- Patch Version: `+semver: patch` or `+semver: fix`


And the following files
- docker-compose.dev.yaml
- docker-compose.yaml


## TRI Checker

The aspects directory contains a TRI Check class that performs validation steps such as checking that necessary tags (Tag Checker) are present. It is automatically used by the template.

In order to transfer it to custom-built CDK applications please do the following:

1. Copy the entire "aspects" directory to the location of your cdk code (same level as the app.py)
2. Import the TRI Checker class by adding the following lines to your app.py file:
``` python
from aspects.TRIChecker import (
    TRIChecker
)
```

3. On the line before the "app.synth()", add the following: "TRIChecker(app)"

This should look like this:
``` python
TRIChecker(app)

app.synth()
```