// import { testAPICall } from "../lib/testAPICall"
"use server"
import { unstable_noStore as noStore } from 'next/cache';

async function testAPICall() {
  // Add noStore() here to prevent the response from being cached.
  // This is equivalent to in fetch(..., {cache: 'no-store'}).
  noStore();
  console.log("Moved to Caching")
  // console.log(process.env.TEST_SECRET)
  let url_to_call = "/api"
  const env = process.env
  if (env.APP_SERVICES_BACKEND_SERVICE_URL) {
    url_to_call = env.APP_SERVICES_BACKEND_SERVICE_URL + url_to_call
  }  

  try {
    console.log(`Fetching remote data from ${url_to_call}`);
    const res = await fetch(url_to_call)
    if (!res.ok) {
      // This will activate the closest `error.js` Error Boundary
      throw new Error('Failed to fetch data')
    }

    return res.json()

  } catch (error) {
    return error
  }
}

export default async function APITester() {
  console.log("SECRET")
  // console.log(process.env.TEST_SECRET)
  const api_response = await testAPICall()
  if (!api_response) {
    return <p className="mt-4 text-gray-400">No data available.</p>;
  }

  console.log(api_response)

  return (
    <>
      <a
        className="App-link"
        href={process.env["APP_SERVICES_BACKEND_SERVICE_URL"]+ "/api"}
        target="_blank"
        rel="noopener noreferrer"
      >
        Backend Url: {process.env["APP_SERVICES_BACKEND_SERVICE_URL"]}/api
      </a>
      <div>
        Backend Response: <pre>{JSON.stringify(api_response, null, 2)}</pre>
      </div>
    </>
  )
}