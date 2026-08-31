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

function cacheKey(probe) {
  return `live:${probe}`
}

async function runtimeCache() {
  try {
    const mod = await import('@vercel/functions')
    if (typeof mod.getCache === 'function') {
      return mod.getCache({ namespace: 'sentinel-demo' })
    }
  } catch {
    // Local Vite / Node: in-memory Map is enough.
  }
  return null
}

async function readBrokenUntil(probe) {
  const fromMemory = liveBrokenUntil.get(probe) || 0
  if (fromMemory > Date.now()) return fromMemory
  const cache = await runtimeCache()
  if (!cache) return 0
  try {
    const stored = await cache.get(cacheKey(probe))
    const until = typeof stored === 'number' ? stored : Number(stored)
    if (Number.isFinite(until) && until > Date.now()) {
      liveBrokenUntil.set(probe, until)
      return until
    }
  } catch {
    return 0
  }
  return 0
}

async function writeBrokenUntil(probe, until) {
  liveBrokenUntil.set(probe, until)
  const cache = await runtimeCache()
  if (!cache) return
  const ttl = Math.max(1, Math.ceil((until - Date.now()) / 1000))
  try {
    await cache.set(cacheKey(probe), until, {
      ttl,
      tags: ['sentinel-demo-live', `probe:${probe}`],
      name: 'demo-live-probe',
    })
  } catch {
    // Keep the in-memory write even if Runtime Cache is unavailable.
  }
}

async function clearBrokenUntil(probe) {
  liveBrokenUntil.delete(probe)
  const cache = await runtimeCache()
  if (!cache) return
  try {
    await cache.delete(cacheKey(probe))
  } catch {
    // ignore
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
 * @returns {Promise<{ status: number, headers: Record<string, string>, body: string } | null>}
 */
export async function handleDemoRequest(requestUrl, method = 'GET') {
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

  if (methodUpper === 'POST' || methodUpper === 'PUT') {
    const until = now + LIVE_TTL_MS
    await writeBrokenUntil(probe, until)
    return json(200, {
      status: 'broken',
      demo: true,
      probe,
      broken_for_seconds: DEMO_LIVE_TTL_SECONDS,
      message: 'Next GET requests return HTTP 503 until the TTL expires.',
    })
  }

  if (methodUpper === 'DELETE') {
    await clearBrokenUntil(probe)
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

  const until = await readBrokenUntil(probe)
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
  Promise.resolve(handleDemoRequest(url, req.method || 'GET'))
    .then((result) => {
      if (!result) {
        next()
        return
      }
      applyDemoResponse(res, result)
    })
    .catch(next)
}
