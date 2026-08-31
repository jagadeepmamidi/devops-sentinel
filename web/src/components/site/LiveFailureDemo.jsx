import { useMemo, useState } from 'react'
import { Check, Copy } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { DEMO_FAIL_PATH, DEMO_LIVE_PATH, INSTALL_COMMAND } from '@/lib/site'

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

export default function LiveFailureDemo() {
  const probe = useDemoProbe()
  const origin = originOf()
  const liveUrl = probe ? `${origin}${DEMO_LIVE_PATH}/${probe}` : ''
  const failUrl = `${origin}${DEMO_FAIL_PATH}`
  const monitorCommand = liveUrl
    ? `sentinel services add site-demo ${liveUrl}\nsentinel monitor site-demo --failure-threshold 1`
    : ''

  const [copied, setCopied] = useState(false)
  const [busy, setBusy] = useState('')
  const [result, setResult] = useState(null)
  const [usedFailFallback, setUsedFailFallback] = useState(false)

  const resultTone = useMemo(() => {
    if (!result) return 'text-muted-foreground'
    if (result.status >= 500) return 'text-destructive'
    if (result.status >= 200 && result.status < 400) return 'text-primary'
    return 'text-foreground'
  }, [result])

  async function copyMonitor() {
    if (!monitorCommand) return
    try {
      await navigator.clipboard.writeText(monitorCommand.replaceAll('\n', ' && '))
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
    try {
      await fetch(liveUrl, { method: 'POST' })
      let response = await fetch(liveUrl)
      let fallback = false
      if (response.ok) {
        response = await fetch(failUrl)
        fallback = true
      }
      setUsedFailFallback(fallback)
      setResult({ status: response.status, body: await readJson(response), url: fallback ? failUrl : liveUrl })
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
    try {
      await fetch(liveUrl, { method: 'DELETE' })
      const response = await fetch(liveUrl)
      setResult({ status: response.status, body: await readJson(response), url: liveUrl })
    } catch (error) {
      setResult({ status: 0, body: { error: error instanceof Error ? error.message : 'request_failed' }, url: liveUrl })
    } finally {
      setBusy('')
    }
  }

  return (
    <div className="terminal-frame min-h-0 justify-start">
      <div className="terminal-frame-header">
        <span>try it / live 503</span>
        <span>after sentinel init</span>
      </div>
      <div className="grid gap-4 pt-8">
        <ol className="grid gap-3 text-sm leading-6 text-muted-foreground">
          <li>
            <span className="text-primary">1.</span> Install and init:{' '}
            <code className="text-foreground">{INSTALL_COMMAND}</code>
            {' · '}
            <code className="text-foreground">sentinel init</code>
          </li>
          <li>
            <span className="text-primary">2.</span> Point the CLI at this page&apos;s live probe
            (healthy until you break it):
          </li>
        </ol>
        <div
          className="flex max-w-full items-start gap-2 border border-border bg-card px-3 py-2 font-mono text-[13px] leading-6"
          role="group"
          aria-label="CLI commands to monitor the live demo endpoint"
        >
          <span className="text-primary" aria-hidden="true">
            $
          </span>
          <code className="min-w-0 flex-1 overflow-x-auto whitespace-pre-wrap text-foreground">
            {monitorCommand || '…'}
          </code>
          <Button type="button" variant="ghost" size="sm" onClick={copyMonitor} disabled={!monitorCommand}>
            {copied ? <Check className="size-4" /> : <Copy className="size-4" />}
            {copied ? 'Copied' : 'Copy'}
          </Button>
        </div>
        <p className="text-sm leading-6 text-muted-foreground">
          <span className="text-primary">3.</span> Leave{' '}
          <code className="text-foreground">sentinel monitor</code> running, then break the
          endpoint. Sentinel should print <code className="text-foreground">DEGRADED | 503</code>.
        </p>
        <div className="flex flex-wrap gap-3">
          <Button type="button" variant="destructive" onClick={breakEndpoint} disabled={!liveUrl || Boolean(busy)}>
            {busy === 'break' ? 'Breaking…' : 'Break this endpoint'}
          </Button>
          <Button type="button" variant="outline" onClick={restoreEndpoint} disabled={!liveUrl || Boolean(busy)}>
            {busy === 'restore' ? 'Restoring…' : 'Restore'}
          </Button>
        </div>
        {result ? (
          <pre
            className={`overflow-x-auto border border-border bg-card p-3 font-mono text-[13px] leading-6 ${resultTone}`}
            aria-live="polite"
          >
            {`HTTP ${result.status || 'ERR'}  ${result.url}\n${JSON.stringify(result.body, null, 2)}`}
          </pre>
        ) : null}
        {usedFailFallback ? (
          <p className="text-xs leading-6 text-muted-foreground">
            This host did not keep the live-probe switch. Use the always-fail URL so the CLI still
            sees HTTP 503:{' '}
            <code className="text-foreground">{failUrl}</code>
          </p>
        ) : (
          <p className="text-xs leading-6 text-muted-foreground">
            Always-on 503 (no button required): <code className="text-foreground">{failUrl || DEMO_FAIL_PATH}</code>
          </p>
        )}
        <span className="sr-only" aria-live="polite">
          {copied ? 'Monitor commands copied to clipboard.' : ''}
          {result ? `Demo endpoint responded with HTTP ${result.status}.` : ''}
        </span>
      </div>
    </div>
  )
}
