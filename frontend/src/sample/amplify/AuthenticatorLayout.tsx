'use client';

import { Authenticator } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';
import { Amplify } from 'aws-amplify';
import { useEffect, useState } from 'react';
import { aws_amplify_config } from './awsConfig';

export default function AuthenticatorLayout( {
    children,
  }: {
    children: React.ReactNode;
  })  {
    
    // When we initially load amplify, we configure the service
    const [ amplifyLoaded, setAmplifyLoading ] = useState(false)
    const [ amplifyNotEnabled, setAmplifyNotEnabled ] = useState(false)
    useEffect(() => {
        const get_aws_configuration = async () => {
            try {
                const response = await aws_amplify_config()
                Amplify.configure(response, {ssr: true});
            } catch (err) {
                // If we have an error 
                console.log(err)
                setAmplifyNotEnabled(true)
            }
            setAmplifyLoading(true)
        }

        get_aws_configuration()
    }, [])

    if (amplifyLoaded) {
        if (amplifyNotEnabled) {
            return <>{children}</>
        } else {
            return (
                <>
                    <Authenticator hideSignUp={false}>
                        <>{children}</>
                    </Authenticator>
                </>
            );
        }
    }


  return null;
}
