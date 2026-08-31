import assert from 'node:assert/strict'
import { test } from 'node:test'
import { handleDemoRequest, normalizeDemoPath } from './demo-api.mjs'

test('ok returns JSON 200', async () => {
  const res = await handleDemoRequest('/api/demo/ok', 'GET')
  assert.equal(res.status, 200)
  assert.equal(JSON.parse(res.body).status, 'ok')
  assert.equal(res.headers['Cache-Control'], 'no-store')
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
  assert.equal(JSON.parse(broke.body).status, 'broken')
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
