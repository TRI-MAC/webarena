"use server"
export const aws_amplify_config = async () : Promise<{}> => {
    if (process.env.AWS_SERVICES_AMPLIFY_ENABLED && process.env.AWS_SERVICES_AMPLIFY_ENABLED.toLowerCase() == "true") {
        return {
            Auth: {
                Cognito: {
                    // REQUIRED - Amazon Cognito Region
                    region: process.env.AWS_SERVICES_AMPLIFY_AUTH_REGION ? process.env.AWS_SERVICES_AMPLIFY_AUTH_REGION : "",

                    // OPTIONAL - Amazon Cognito User Pool ID 
                    userPoolId: process.env.AWS_SERVICES_AMPLIFY_AUTH_USER_POOL_ID ? process.env.AWS_SERVICES_AMPLIFY_AUTH_USER_POOL_ID : "",

                    // OPTIONAL - Amazon Cognito Web Client ID (26-char alphanumeric string)
                    userPoolClientId: process.env.AWS_SERVICES_AMPLIFY_AUTH_WEB_CLIENT_ID ? process.env.AWS_SERVICES_AMPLIFY_AUTH_WEB_CLIENT_ID : "",

                    // OPTIONAL - Enforce user authentication prior to accessing AWS resources or not
                    mandatorySignIn: false
                }
            }
        }
    }
    throw Error("Amplify Not enabled")
};