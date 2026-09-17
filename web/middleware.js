import { next } from '@vercel/functions'

/**
 * Claim /api/demo so the Vite SPA rewrite cannot swallow the probe URLs.
 *
 * Do not generate the JSON here. Edge isolates (and regional Runtime Cache)
 * are not shared with `sentinel monitor`, so a Break click would show HTTP 503
 * in the browser while the CLI kept printing HEALTHY 200. `next()` continues
 * to the Node.js function in api/demo/[...path].js, which stores probe state
 * in one region.
 */
export default function middleware() {
  return next({
    headers: {
      'Cache-Control': 'no-store, no-cache, must-revalidate',
      'CDN-Cache-Control': 'no-store',
      'Vercel-CDN-Cache-Control': 'no-store',
    },
  })
}

export const config = {
  matcher: '/api/demo/:path*',
}
