# Configuration and Variable User Guide
Variables for the template web application are stored in environment specific variable files within this directory. Files should be named according to their environment using .yaml extension. 

The name of the desired deployed environment is loaded in [app.py](../cdk/app.py) as CDK context and this is used by the omegaconf python library to load the contents of the yaml file as dictionary variables accessible by CDK python code. 

Accessing these variables can be done universally by leveraging omegaconf to load the contents of the file. 

Most of the functions written to handle, load and interact with configuration variables can be found in [parameters.py](../cdk/cdk/parameters.py)

## App Name Guidelines
The app_name that is added to development.yaml file will reflect in the names of the resources created by the AWS CDK. AWS enforces certain naming restrictions across AWS resources. An app_name that is not in compliance will result in a failed deployment to AWS. Because of this, the template will automatically modify the app_name so that it will be in compliance with AWS prior to deployment.

The naming requirements are as follows
1. Maximum length of 40 characters
2. Lowercase only
3. Hyphens only, underscores will be replaced by hyphens
4. No two or more consecutive hyphens (e.g. "--")

Before finalizing an app_name name for the repository, click [here](https://docs.google.com/spreadsheets/d/1XU5gGJLh2X5mhV2gdL-vr6C9Nkg9NWx1naw9noKOxXw/edit?usp=sharing) to test the app_name. The tester will show what a given app_name would be converted to by the template. Failure to test the app_name beforehand may result in resources that do not have a name that is expected.

## Tagging 

For administrative reasons, we also need to fill out the tags correctly in each of the config file for the deployment to be successful.

tags:

- tri.owner.email: "REPLACE_WITH_EMAIL" #the email of the person who launched this resource and is responsible for maintaining, stopping, and terminating this resource
- tri.project: "REPLACE_WITH_PROJECT_CODE" #a special code for each project (or department) that TRI Finance uses to determine which department to bill for this resource https://toyotaresearchinstitute.atlassian.net/wiki/spaces/HSS/pages/2913894417/Tagging+AWS+Resources+for+HCAI#tri.project
- hcai.projectname: "REPLACE_WITH_PROJECT_NAME" #the name of the HCAI project that this AWS resource is used for
- hcai.stakeholder.email: "REPLACE_WITH_EMAIL" #the email of the HCAI project stakeholder

## Secret Key Guidelines
The flow for using secrets is as follows
1. Add secret key name (with no value) to the appropriate app_secrets section of the desired config file.
2. Triggering a deploy will now create a new secret in AWS Secrets Manager with this name. Navigate to Secrets Manager and input the value.
3. Trigger a deploy will load the secret value in the appropriate container. 

## Environment Variables Guidelines
The flow for adding environment variables is as follows
1. Add the environment variable and key to the corresponding service section, for example a frontend environment variable should be added to the Frontend section of the app_environments variable segment of the [development.yaml](development.yaml).
2. These variables are iterated through, put into a python dictionary and then uploaded into SSM Paramstore for access by the requisite container service. A working example of this can be found [here](https://github.com/TRI-MAC/storybook-ecs/blob/initial-configuration/config/local.yaml#L87)


