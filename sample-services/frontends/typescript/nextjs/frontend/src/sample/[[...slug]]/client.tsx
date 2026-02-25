'use client'
 
import React from 'react'
import dynamic from 'next/dynamic'
 
// We use dynamic import to import the entirety of the Create-REact-App application
// Please change this to import your current "App" file
// const App = dynamic(() => import('../../App'), { ssr: false })
 
export function ClientOnly() {
    return <>SAMPLE</>
    //   return <App />
}