from constructs import Construct

from typing import (
    Mapping,
    Optional
)

# CDK imports
from aws_cdk import (
    aws_certificatemanager as acm,
    aws_cognito as cognito,
    Tags
)

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass
from dataclasses import field

@dataclass(config=ConfigDict(arbitrary_types_allowed=True),kw_only=True)
class CognitoParameters:
    """
    Parameters for Cognito Service

    Parameters required for Cognito Service

    enabled : bool
        Whether cognito construct should be deployed
    cert : aws_certificatemanager.Certificate
        The certificate to use with the Cognito user Pool
    callback_urls : list[str]
        The list of callback urls that Cognito will accept. Note that if the cert is not provided then these will not be used
    
    """
    enabled : Optional[bool] = False
    cert : Optional[acm.Certificate] = None
    callback_urls : Optional[list[str]] = field(default_factory=list[str])


class Cognito(Construct):
    """
    Cognito Construct

    The Cognito Construct adds the following infrastructure:
    - User Pool
    - User Pool Client for the Front End Web Application

    Attributes:
    - user_pool : aws_cognito.UserPool
        The User Pool created
    - user_pool_client : aws_cognito.UserPoolClient
    - scopes : [cognito.OAuthScope]
        The OAuthScopes for the user pool
    - cognito_callback_urls : list[str]
        The List of callback urls setup for the user pool

    """


    def __init__(self, scope: Construct, id: str, cognito_params : CognitoParameters, **kwargs) -> None:
        """
        Creates the Fargate Service

        Creates the fargate service with the networking components listed above
        
        Parameters:
            scope: Construct
                The parent construct in which the networking construct will be deployed.
            id : string
                Reference for the networking stack
            cognito_params : CognitoParameters
                Parameters required for the Cognito Construct
        """

        super().__init__(scope, id, **kwargs)

        self.user_pool = cognito.UserPool(self, "UserPool")

        self.scopes = [
            cognito.OAuthScope.PROFILE,
            cognito.OAuthScope.PHONE,
            cognito.OAuthScope.EMAIL,
            cognito.OAuthScope.OPENID,
            cognito.OAuthScope.COGNITO_ADMIN
        ]

        # If we have a cert arn, we have callback_urls
        self.cognito_callback_urls = []

        if cognito_params.cert and cognito_params.callback_urls:
            for callback_url in cognito_params.callback_urls:
                self.cognito_callback_urls.append(callback_url)
        else:
            # TODO: Maybe change this to do the callback urls
            # If we don't have a certificate, we just add https://example.com instead of the given callback urls
            self.cognito_callback_urls.append("https://example.com")

        self.user_pool_client = self.user_pool.add_client("WebClient",
            user_pool_client_name="web_app_client",
            o_auth=cognito.OAuthSettings(
                scopes=self.scopes,
                callback_urls=self.cognito_callback_urls,
            )
        )

        Tags.of(self).add("tri.resource.class", "application");