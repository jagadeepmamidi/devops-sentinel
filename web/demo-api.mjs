/** Shared HTTP handlers for the public CLI demo endpoints. */

export const DEMO_LIVE_TTL_SECONDS = 120
const LIVE_TTL_MS = DEMO_LIVE_TTL_SECONDS * 1000
const liveBrokenUntil = new Map()

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, HEAD, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Cache-Control': 'no-store',
  'Content-Type': 'application/json; charset=utf-8',
}

function json(status, payload) {
  return {
    status,
    headers: { ...CORS_HEADERS },
    body: JSON.stringify(payload),
  }
}

export function normalizeDemoPath(requestUrl) {
  const url = new URL(requestUrl, 'http://sentinel.demo')
  let pathname = url.pathname.replace(/\/+$/, '') || '/'
  if (pathname === '/ok' || pathname === '/fail' || pathname.startsWith('/live')) {
    pathname = `/api/demo${pathname}`
  }
  return { pathname, search: url.search }
}

/**
 * @param {string} requestUrl
 * @param {string} [method]
 * @returns {{ status: number, headers: Record<string, string>, body: string } | null}
 */
export function handleDemoRequest(requestUrl, method = 'GET') {
  if (!requestUrl) return null

  let pathname
  try {
    pathname = normalizeDemoPath(requestUrl).pathname
  } catch {
    return null
  }
  if (!pathname.startsWith('/api/demo')) return null

  const methodUpper = String(method || 'GET').toUpperCase()
  if (methodUpper === 'OPTIONS') {
    return { status: 204, headers: { ...CORS_HEADERS }, body: '' }
  }

  if (pathname === '/api/demo/ok') {
    if (methodUpper !== 'GET' && methodUpper !== 'HEAD') {
      return json(405, { status: 'error', error: 'method_not_allowed' })
    }
    return json(200, {
      status: 'ok',
      demo: true,
      service: 'sentinel-site-demo',
      endpoint: 'ok',
    })
  }

  if (pathname === '/api/demo/fail') {
    if (methodUpper !== 'GET' && methodUpper !== 'HEAD') {
      return json(405, { status: 'error', error: 'method_not_allowed' })
    }
    return json(503, {
      status: 'error',
      demo: true,
      service: 'sentinel-site-demo',
      error: 'intentional_failure',
      endpoint: 'fail',
    })
  }

  const liveMatch = pathname.match(/^\/api\/demo\/live(?:\/([A-Za-z0-9_-]{1,64}))?$/)
  if (!liveMatch) {
    return json(404, { status: 'error', demo: true, error: 'unknown_demo_endpoint' })
  }

  const probe = liveMatch[1] || 'default'
  const now = Date.now()
  const until = liveBrokenUntil.get(probe) || 0

  if (methodUpper === 'POST' || methodUpper === 'PUT') {
    liveBrokenUntil.set(probe, now + LIVE_TTL_MS)
    return json(200, {
      status: 'broken',
      demo: true,
      probe,
      broken_for_seconds: DEMO_LIVE_TTL_SECONDS,
      message: 'Next GET requests return HTTP 503 until the TTL expires.',
    })
  }

  if (methodUpper === 'DELETE') {
    liveBrokenUntil.delete(probe)
    return json(200, {
      status: 'ok',
      demo: true,
      probe,
      message: 'Endpoint restored to HTTP 200.',
    })
  }

  if (methodUpper !== 'GET' && methodUpper !== 'HEAD') {
    return json(405, { status: 'error', error: 'method_not_allowed' })
  }

  if (until > now) {
    return json(503, {
      status: 'error',
      demo: true,
      service: 'sentinel-site-demo',
      error: 'broken_by_button',
      probe,
      remaining_seconds: Math.ceil((until - now) / 1000),
      endpoint: 'live',
    })
  }

  return json(200, {
    status: 'ok',
    demo: true,
    service: 'sentinel-site-demo',
    probe,
    endpoint: 'live',
  })
}

export function applyDemoResponse(res, result) {
  res.statusCode = result.status
  for (const [key, value] of Object.entries(result.headers)) {
    res.setHeader(key, value)
  }
  res.end(result.body)
}

export function demoApiMiddleware(req, res, next) {
  const url = req.url || '/'
  const pathOnly = url.split('?')[0]
  if (!pathOnly.startsWith('/api/demo')) {
    next()
    return
  }
  const result = handleDemoRequest(url, req.method || 'GET')
  if (!result) {
    next()
    return
  }
  applyDemoResponse(res, result)
}
