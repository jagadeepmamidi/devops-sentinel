import { useMemo, useState } from 'react'
import { Check, Copy } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { DEMO_FAIL_PATH, DEMO_LIVE_PATH, INSTALL_COMMAND } from '@/lib/site'
import TerminalWindow from './TerminalWindow'

const PROBE_KEY = 'sentinel-demo-probe'

function readProbe() {
  if (typeof window === 'undefined') return ''
  let id = sessionStorage.getItem(PROBE_KEY)
  if (!id || !/^[A-Za-z0-9_-]{8,64}$/.test(id)) {
    id = crypto.randomUUID()
    sessionStorage.setItem(PROBE_KEY, id)
  }
  return id
}

function useDemoProbe() {
  const [probe] = useState(readProbe)
  return probe
}

function originOf() {
  if (typeof window === 'undefined') return ''
  return window.location.origin
}

function isSpaDocument(response, body) {
  const contentType = response.headers.get('content-type') || ''
  if (contentType.includes('text/html')) return true
  if (typeof body?.raw === 'string' && /^\s*</.test(body.raw)) return true
  return false
}

function Prompt({ children }) {
  return (
    <div className="terminal-cmd">
      <span className="terminal-cmd-prompt" aria-hidden="true">
        $
      </span>
      <code className="min-w-0 overflow-x-auto whitespace-pre-wrap break-all text-foreground">{children}</code>
    </div>
  )
}

export default function LiveFailureDemo() {
  const probe = useDemoProbe()
  const origin = originOf()
  const liveUrl = probe ? `${origin}${DEMO_LIVE_PATH}/${probe}` : ''
  const failUrl = `${origin}${DEMO_FAIL_PATH}`
  const monitorLines = liveUrl
    ? [
        `sentinel services add site-demo ${liveUrl} --interval 5`,
        'sentinel monitor site-demo --failure-threshold 1',
      ]
    : []
  const monitorCommand = monitorLines.join('\n')

  const [copied, setCopied] = useState(false)
  const [busy, setBusy] = useState('')
  const [result, setResult] = useState(null)
  const [usedFailFallback, setUsedFailFallback] = useState(false)
  const [spaMiss, setSpaMiss] = useState(false)
  const [memoryOnlyBreak, setMemoryOnlyBreak] = useState(false)

  const resultTone = useMemo(() => {
    if (!result) return 'text-muted-foreground'
    if (spaMiss) return 'text-destructive'
    if (result.status >= 500) return 'text-destructive'
    if (result.status >= 200 && result.status < 400) return 'text-primary'
    return 'text-foreground'
  }, [result, spaMiss])

  const status = useMemo(() => {
    if (spaMiss) return { tone: 'bad', label: 'html miss' }
    if (!result) return { tone: 'idle', label: 'probe idle' }
    if (result.status >= 500) return { tone: 'bad', label: `${result.status} broken` }
    if (result.status >= 200 && result.status < 400) return { tone: 'ok', label: `${result.status} ok` }
    return { tone: 'idle', label: `http ${result.status || 'err'}` }
  }, [result, spaMiss])

  async function copyMonitor() {
    if (!monitorCommand) return
    try {
      await navigator.clipboard.writeText(monitorCommand)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1800)
    } catch {
      setCopied(false)
    }
  }

  async function readJson(response) {
    const text = await response.text()
    try {
      return JSON.parse(text)
    } catch {
      return { raw: text }
    }
  }

  async function breakEndpoint() {
    if (!liveUrl) return
    setBusy('break')
    setUsedFailFallback(false)
    setSpaMiss(false)
    setMemoryOnlyBreak(false)
    try {
      const posted = await fetch(liveUrl, { method: 'POST', cache: 'no-store' })
      const postedBody = await readJson(posted)
      setMemoryOnlyBreak(postedBody?.durable === false)
      if (isSpaDocument(posted, postedBody) || posted.status === 405) {
        setSpaMiss(true)
        setResult({
          status: posted.status,
          url: liveUrl,
          body: {
            error: 'demo_api_not_routed',
            message:
              'This host served the website HTML (HTTP 200) instead of the demo API. Sentinel treats that as HEALTHY. Wait for /api/demo to be routed in front of the SPA, then try Break again.',
          },
        })
        return
      }
      let response = await fetch(liveUrl, { cache: 'no-store' })
      let body = await readJson(response)
      let fallback = false
      if (response.ok || isSpaDocument(response, body)) {
        response = await fetch(failUrl, { cache: 'no-store' })
        body = await readJson(response)
        fallback = !isSpaDocument(response, body)
        if (!fallback) {
          setSpaMiss(true)
          setResult({
            status: response.status,
            url: liveUrl,
            body: {
              error: 'demo_api_not_routed',
              message:
                'Break did not stick: GET still returned the homepage HTML. The CLI will stay HEALTHY until /api/demo/live returns JSON 503.',
            },
          })
          return
        }
      }
      setUsedFailFallback(fallback)
      setResult({ status: response.status, body, url: fallback ? failUrl : liveUrl })
    } catch (error) {
      setResult({ status: 0, body: { error: error instanceof Error ? error.message : 'request_failed' }, url: liveUrl })
    } finally {
      setBusy('')
    }
  }

  async function restoreEndpoint() {
    if (!liveUrl) return
    setBusy('restore')
    setUsedFailFallback(false)
    setSpaMiss(false)
    setMemoryOnlyBreak(false)
    try {
      await fetch(liveUrl, { method: 'DELETE', cache: 'no-store' })
      const response = await fetch(liveUrl, { cache: 'no-store' })
      const body = await readJson(response)
      if (isSpaDocument(response, body)) {
        setSpaMiss(true)
        setResult({
          status: response.status,
          url: liveUrl,
          body: {
            error: 'demo_api_not_routed',
            message: 'Restore hit the homepage HTML, not the demo API.',
          },
        })
        return
      }
      setResult({ status: response.status, body, url: liveUrl })
    } catch (error) {
      setResult({ status: 0, body: { error: error instanceof Error ? error.message : 'request_failed' }, url: liveUrl })
    } finally {
      setBusy('')
    }
  }

  const hint = spaMiss
    ? `# CLI stays HEALTHY: this URL returned homepage HTML, not JSON 503.`
    : usedFailFallback
      ? `# live probe did not stick. always-fail: ${failUrl}`
      : memoryOnlyBreak
        ? `# break only stuck in this browser. if CLI stays 200, use ${failUrl || DEMO_FAIL_PATH}`
        : `# always-on 503 (no button): ${failUrl || DEMO_FAIL_PATH}`

  return (
    <TerminalWindow title="try it / live 503" status={status}>
      <div className="terminal-session">
        <p className="terminal-comment"># install and init</p>
        <Prompt>{INSTALL_COMMAND}</Prompt>
        <Prompt>sentinel init</Prompt>

        <p className="terminal-comment mt-3">
          # point the CLI at this probe. PowerShell: run each line separately. && is invalid there.
        </p>
        <div
          className="grid gap-1 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-start sm:gap-3"
          role="group"
          aria-label="CLI commands to monitor the live demo endpoint"
        >
          <div className="grid min-w-0 gap-1">
            {monitorLines.length ? (
              monitorLines.map((line) => <Prompt key={line}>{line}</Prompt>)
            ) : (
              <Prompt>…</Prompt>
            )}
          </div>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="justify-self-start sm:mt-0.5"
            onClick={copyMonitor}
            disabled={!monitorCommand}
          >
            {copied ? <Check className="size-4" /> : <Copy className="size-4" />}
            {copied ? 'Copied' : 'Copy'}
          </Button>
        </div>

        <p className="terminal-comment mt-3">
          # leave sentinel monitor running, then break. next check (every 5s) should print DEGRADED | 503. stays
          broken for five minutes.
        </p>

        <div className="relative z-10 mt-3 flex flex-wrap gap-2">
          <Button type="button" variant="destructive" size="sm" onClick={breakEndpoint} disabled={!liveUrl || Boolean(busy)}>
            {busy === 'break' ? 'Breaking...' : 'Break this endpoint'}
          </Button>
          <Button type="button" variant="outline" size="sm" onClick={restoreEndpoint} disabled={!liveUrl || Boolean(busy)}>
            {busy === 'restore' ? 'Restoring...' : 'Restore'}
          </Button>
        </div>

        {result ? (
          <pre className={`mt-3 overflow-x-hidden whitespace-pre-wrap break-all ${resultTone}`} aria-live="polite">
            {`HTTP ${result.status || 'ERR'}  ${result.url}\n${JSON.stringify(result.body, null, 2)}`}
          </pre>
        ) : (
          <p className="mt-3 text-primary">
            ${' '}
            <span className="terminal-caret" aria-hidden="true" />
          </p>
        )}

        <p className="terminal-comment mt-3">{hint}</p>
        <span className="sr-only" aria-live="polite">
          {copied ? 'Monitor commands copied to clipboard.' : ''}
          {result ? `Demo endpoint responded with HTTP ${result.status}.` : ''}
        </span>
      </div>
    </TerminalWindow>
  )
}
