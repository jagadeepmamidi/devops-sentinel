import { createReadStream, existsSync, statSync } from 'node:fs'
import { createServer } from 'node:http'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { handleDemoRequest } from './demo-api.mjs'

const rootDir = path.dirname(fileURLToPath(import.meta.url))
const distDir = path.join(rootDir, 'dist')
const port = Number.parseInt(process.env.PORT || '3000', 10)
const host = '0.0.0.0'

const MIME = {
  '.css': 'text/css; charset=utf-8',
  '.html': 'text/html; charset=utf-8',
  '.ico': 'image/x-icon',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.map': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.txt': 'text/plain; charset=utf-8',
  '.webp': 'image/webp',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
}

function safeFile(urlPath) {
  const decoded = decodeURIComponent((urlPath || '/').split('?')[0])
  const relative = decoded.replace(/^\/+/, '')
  const resolved = path.normalize(path.join(distDir, relative))
  if (!resolved.startsWith(distDir)) return null
  return resolved
}

function sendFile(res, filePath, status = 200) {
  const ext = path.extname(filePath)
  const immutable = ext !== '.html' && ext !== ''
  res.writeHead(status, {
    'Content-Type': MIME[ext] || 'application/octet-stream',
    'Cache-Control': immutable ? 'public, max-age=31536000, immutable' : 'no-store',
    'X-Frame-Options': 'DENY',
  })
  createReadStream(filePath).pipe(res)
}

const server = createServer((req, res) => {
  const demo = handleDemoRequest(req.url || '/', req.method || 'GET')
  if (demo) {
    res.writeHead(demo.status, {
      'X-Frame-Options': 'DENY',
      ...demo.headers,
    })
    res.end(demo.body)
    return
  }

  const filePath = safeFile(req.url || '/')
  if (filePath && existsSync(filePath) && statSync(filePath).isFile()) {
    sendFile(res, filePath)
    return
  }

  const index = path.join(distDir, 'index.html')
  if (existsSync(index)) {
    sendFile(res, index)
    return
  }

  res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' })
  res.end('Not found')
})

server.listen(port, host, () => {
  console.log(`sentinel web listening on http://${host}:${port}`)
})
