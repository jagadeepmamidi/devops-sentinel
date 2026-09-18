import assert from 'node:assert/strict'
import { afterEach, test } from 'node:test'
import {
  DEMO_LIVE_TTL_SECONDS,
  forgetLocalBrokenState,
  handleDemoRequest,
  normalizeDemoPath,
  parseBrokenUntil,
  setDemoCacheForTests,
} from './demo-api.mjs'

afterEach(() => {
  setDemoCacheForTests(null)
})

test('ok returns JSON 200', async () => {
  const res = await handleDemoRequest('/api/demo/ok', 'GET')
  assert.equal(res.status, 200)
  assert.equal(JSON.parse(res.body).status, 'ok')
  assert.equal(res.headers['Cache-Control'], 'no-store, no-cache, must-revalidate')
  assert.equal(res.headers['Vercel-CDN-Cache-Control'], 'no-store')
})

test('fail returns JSON 503', async () => {
  const res = await handleDemoRequest('/api/demo/fail', 'GET')
  assert.equal(res.status, 503)
  const body = JSON.parse(res.body)
  assert.equal(body.error, 'intentional_failure')
  assert.equal(body.demo, true)
})

test('unknown demo path returns 404', async () => {
  const res = await handleDemoRequest('/api/demo/nope', 'GET')
  assert.equal(res.status, 404)
})

test('non-demo paths are ignored', async () => {
  assert.equal(await handleDemoRequest('/docs', 'GET'), null)
  assert.equal(await handleDemoRequest('/api/services', 'GET'), null)
})

test('live probe is healthy until broken, then restores', async () => {
  const path = '/api/demo/live/probe-unit-test'
  assert.equal((await handleDemoRequest(path, 'GET')).status, 200)
  const broke = await handleDemoRequest(path, 'POST')
  assert.equal(broke.status, 200)
  const brokeBody = JSON.parse(broke.body)
  assert.equal(brokeBody.status, 'broken')
  assert.equal(brokeBody.broken_for_seconds, DEMO_LIVE_TTL_SECONDS)
  const failed = await handleDemoRequest(path, 'GET')
  assert.equal(failed.status, 503)
  assert.equal(JSON.parse(failed.body).error, 'broken_by_button')
  assert.equal((await handleDemoRequest(path, 'DELETE')).status, 200)
  assert.equal((await handleDemoRequest(path, 'GET')).status, 200)
})

test('live probes are isolated', async () => {
  await handleDemoRequest('/api/demo/live/one', 'POST')
  assert.equal((await handleDemoRequest('/api/demo/live/two', 'GET')).status, 200)
  assert.equal((await handleDemoRequest('/api/demo/live/one', 'GET')).status, 503)
})

test('OPTIONS is allowed for CORS preflight', async () => {
  const res = await handleDemoRequest('/api/demo/fail', 'OPTIONS')
  assert.equal(res.status, 204)
  assert.equal(res.headers['Access-Control-Allow-Origin'], '*')
})

test('vercel leaf paths normalize under /api/demo', async () => {
  assert.equal(normalizeDemoPath('/fail').pathname, '/api/demo/fail')
  assert.equal(normalizeDemoPath('/live/abc').pathname, '/api/demo/live/abc')
  assert.equal((await handleDemoRequest('/fail', 'GET')).status, 503)
})

test('parseBrokenUntil accepts number, string, and wrapped cache values', () => {
  const until = Date.now() + 60_000
  assert.equal(parseBrokenUntil(until), until)
  assert.equal(parseBrokenUntil(String(until)), until)
  assert.equal(parseBrokenUntil({ value: String(until) }), until)
  assert.equal(parseBrokenUntil({ until }), until)
  assert.equal(parseBrokenUntil(null), 0)
  assert.equal(parseBrokenUntil('not-a-number'), 0)
})

test('http POST then GET returns JSON 503', async () => {
  const { createServer } = await import('node:http')
  const { demoApiMiddleware } = await import('./demo-api.mjs')
  const server = createServer((req, res) => {
    demoApiMiddleware(req, res, () => {
      res.statusCode = 404
      res.end('miss')
    })
  })
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve))
  const { port } = server.address()
  const base = `http://127.0.0.1:${port}/api/demo/live/http-test`
  try {
    assert.equal((await fetch(base)).status, 200)
    assert.equal((await fetch(base, { method: 'POST' })).status, 200)
    const failed = await fetch(base)
    assert.equal(failed.status, 503)
    assert.equal((await failed.json()).error, 'broken_by_button')
    assert.equal((await fetch(`http://127.0.0.1:${port}/api/demo/fail`)).status, 503)
  } finally {
    await new Promise((resolve, reject) => server.close((err) => (err ? reject(err) : resolve())))
  }
})

test('broken state is visible after an isolate miss when Runtime Cache holds it', async () => {
  const store = new Map()
  setDemoCacheForTests({
    async get(key) {
      return store.get(key)
    },
    async set(key, value) {
      store.set(key, value)
    },
    async delete(key) {
      store.delete(key)
    },
  })
  const path = '/api/demo/live/probe-cross-isolate'
  try {
    const broke = await handleDemoRequest(path, 'POST')
    assert.equal(JSON.parse(broke.body).durable, true)
    forgetLocalBrokenState('probe-cross-isolate')
    const failed = await handleDemoRequest(path, 'GET')
    assert.equal(failed.status, 503)
    assert.equal(JSON.parse(failed.body).error, 'broken_by_button')
  } finally {
    setDemoCacheForTests(null)
    forgetLocalBrokenState('probe-cross-isolate')
  }
})
