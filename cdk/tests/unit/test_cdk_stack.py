# # CDK imports
# import aws_cdk as core
# import aws_cdk.assertions as assertions
# from cdk.cdk_stack import CdkStack

# # Other imports
# import logging

# from omegaconf import OmegaConf

# # Because we are referencing existing resources, we require pulling the configuration for performing the tests
# deploy_env = "development" 
# conf = OmegaConf.load("../config/{0}.yaml".format(deploy_env))

# # example tests. To run these tests, uncomment this file along with the example
# # resource in cdk/cdk_stack.py

# ################ S3 DATA Bucket TESTS ##################
# def test_s3_bucket_presence():
#     app = core.App()
#     stack = CdkStack(app, "cdk",
#         env=core.Environment(account=conf.aws.account, region=conf.aws.region),
#         deploy_env=deploy_env,
#         image_tag="latest"
#     )
#     template = assertions.Template.from_stack(stack)
#     template.has_resource_properties("AWS::S3::Bucket",
#         {
            
#         }
#     )

# def test_s3_bucket_allows_back_end_service_communication():
#     app = core.App()
#     stack = CdkStack(app, "cdk",
#         env=core.Environment(account=conf.aws.account, region=conf.aws.region),
#         deploy_env=deploy_env,
#         image_tag="latest"
#     )
#     template = assertions.Template.from_stack(stack)
#     # This checks the policy document to ensure that we have the proper s3 permissions
#     expected_s3_permissions = [
#         "s3:Abort*",
#         "s3:DeleteObject*",
#         "s3:GetBucket*",
#         "s3:GetObject*",
#         "s3:List*",
#         "s3:PutObject",
#         "s3:PutObjectLegalHold",
#         "s3:PutObjectRetention",
#         "s3:PutObjectTagging",
#         "s3:PutObjectVersionTagging"
#     ]

#     for current_permission in expected_s3_permissions:
#         # We check if the template policy document has that element
#         # We check that the role matches the policy
#         # And that we have the proper permissions
#         # We want to check that the entire object is good because we need to verify that the target bucket is valid
#         template.has_resource_properties("AWS::IAM::Policy",
#             {
#                 "Roles": assertions.Match.array_with([
#                     stack.resolve(stack.back_end_fargate_service.task_definition.task_role.role_name)
#                 ]),
#                 "PolicyDocument": {
#                     "Statement": assertions.Match.array_with([
#                         assertions.Match.object_like(
#                             {
#                                 "Action": assertions.Match.array_with(
#                                     [ current_permission ]
#                                 ),
#                                 "Effect": "Allow",
#                                 "Resource": [
#                                     stack.resolve(stack.storage.data_bucket.bucket_arn),
#                                     {
#                                         "Fn::Join": [
#                                             "",
#                                             [
#                                                 stack.resolve(stack.storage.data_bucket.bucket_arn),
#                                                 "/*"
#                                             ]
#                                         ]                                
#                                     }
#                                 ]
#                             }
#                         )
#                     ]),
#                     "Version": "2012-10-17"
#                 },
#             }                          
#         )

# ################ DynamoDB TESTS ##################
# def test_dynamodb_table_presence():
#     if conf.dynamodb:
#         app = core.App()
#         stack = CdkStack(app, "cdk",
#             env=core.Environment(account=conf.aws.account, region=conf.aws.region),
#             deploy_env=deploy_env,
#             image_tag="latest"
#         )
#         template = assertions.Template.from_stack(stack)
#         template.has_resource_properties("AWS::DynamoDB::Table",
#             {
#                 "TableName": conf.aws_services.dynamodb.table_name
#             }
#         )

# def test_dynamodb_table_allows_back_end_service_communication():
#     if conf.dynamodb:
#         app = core.App()
#         stack = CdkStack(app, "cdk",
#             env=core.Environment(account=conf.aws.account, region=conf.aws.region),
#             deploy_env=deploy_env,
#             image_tag="latest"
#         )
#         template = assertions.Template.from_stack(stack)
#         # This checks the policy document to ensure that we have the proper s3 permissions
#         expected_dynamodb_permissions = [
#             "dynamodb:BatchGetItem",
#             "dynamodb:BatchWriteItem",
#             "dynamodb:ConditionCheckItem",
#             "dynamodb:DeleteItem",
#             "dynamodb:DescribeTable",
#             "dynamodb:GetItem",
#             "dynamodb:GetRecords",
#             "dynamodb:GetShardIterator",
#             "dynamodb:PutItem",
#             "dynamodb:Query",
#             "dynamodb:Scan",
#             "dynamodb:UpdateItem"
#         ]

#         for current_permission in expected_dynamodb_permissions:
#             # We check if the template policy document has that element
#             # We check that the role matches the policy
#             # And that we have the proper permissions
#             # We want to check that the entire object is good because we need to verify that the target bucket is valid
#             template.has_resource_properties("AWS::IAM::Policy",
#                 {
#                     "Roles": assertions.Match.array_with([
#                         stack.resolve(stack.back_end_fargate_service.task_definition.task_role.role_name)
#                     ]),
#                     "PolicyDocument": {
#                         "Statement": assertions.Match.array_with([
#                             assertions.Match.object_like(
#                                 {
#                                     "Action": assertions.Match.array_with(
#                                         [ current_permission ]
#                                     ),
#                                     "Effect": "Allow",
#                                     "Resource": assertions.Match.array_with([
#                                         stack.resolve(stack.storage.dynamodb_table.table_arn)
#                                     ])
#                                 }
#                             )
#                         ]),
#                         "Version": "2012-10-17"
#                     },
#                 }                          
#             )