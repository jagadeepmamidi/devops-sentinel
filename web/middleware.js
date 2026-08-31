import { handleDemoRequest } from './demo-api.mjs'

export default async function middleware(request) {
  const result = await handleDemoRequest(request.url, request.method)
  if (!result) return
  return new Response(result.body, {
    status: result.status,
    headers: result.headers,
  })
}

export const config = {
  matcher: '/api/demo/:path*',
}
