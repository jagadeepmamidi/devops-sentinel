import { handleDemoRequest, applyDemoResponse } from '../../demo-api.mjs'

export default function handler(req, res) {
  const result = handleDemoRequest(req.url || '/', req.method || 'GET')
  if (!result) {
    res.statusCode = 404
    res.setHeader('Content-Type', 'application/json; charset=utf-8')
    res.setHeader('Cache-Control', 'no-store')
    res.end(JSON.stringify({ status: 'error', demo: true, error: 'unknown_demo_endpoint' }))
    return
  }
  applyDemoResponse(res, result)
}
