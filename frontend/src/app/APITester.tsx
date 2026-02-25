export default async function APITester() {

  let url_to_call = "/api"
  const env = process.env
  console.log("api call")
  console.log(env.APP_SERVICES_BACKEND_SERVICE_URL)
  if (env.APP_SERVICES_BACKEND_SERVICE_URL) {
    url_to_call = env.APP_SERVICES_BACKEND_SERVICE_URL + url_to_call
  }  else {
    // Unless there is a specific app_service_backend_service_url to call, we call the APP_URL which is built in
    url_to_call = env.APP_URL + url_to_call
  }
  console.log(url_to_call)
  
  const res = await fetch(url_to_call, { cache: 'no-store' })
  
  console.log(res)

  if (!res.ok) {
    return (
      <div>
        An error occured - please try again
      </div>
    )
  }

  const data = await res.json()
  console.log(data)
  return (
    <div>
      {data.message}
    </div>
  )
}