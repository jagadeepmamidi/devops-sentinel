import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import SiteTopNav from '../components/site/SiteTopNav'
import SiteFooter from '../components/site/SiteFooter'
import './CliAuth.css'

function buildSupabaseAuthorizeUrl(supabaseUrl, redirectUri, provider = 'email', state = '') {
  const base = `${supabaseUrl.replace(/\/$/, '')}/auth/v1/authorize`
  const params = new URLSearchParams({
    provider,
    redirect_to: redirectUri,
  })

  if (state) {
    params.set('state', state)
  }

  return `${base}?${params.toString()}`
}

const NAV_LINKS = [
  { to: '/docs', label: 'Docs' },
  { to: '/', label: 'Home' },
]

const FOOTER_LINKS = [
  { to: '/terms', label: 'Terms' },
  { to: '/privacy', label: 'Privacy' },
]

export default function CliAuth() {
  const [searchParams] = useSearchParams()
  const [copied, setCopied] = useState(false)

  const supabaseUrl = searchParams.get('supabase_url') || import.meta.env.VITE_SUPABASE_URL || ''
  const redirectUri = searchParams.get('redirect_uri') || 'http://localhost:54321/callback'
  const state = searchParams.get('state') || ''
  const flow = searchParams.get('source') || 'cli'

  const hasConfig = Boolean(supabaseUrl && redirectUri)
  const emailAuthUrl = hasConfig
    ? buildSupabaseAuthorizeUrl(supabaseUrl, redirectUri, 'email', state)
    : '#'
  const githubAuthUrl = hasConfig
    ? buildSupabaseAuthorizeUrl(supabaseUrl, redirectUri, 'github', state)
    : '#'

  const copyDeviceCommand = async () => {
    try {
      await navigator.clipboard.writeText('sentinel login --device')
      setCopied(true)
      setTimeout(() => setCopied(false), 1600)
    } catch {
      setCopied(false)
    }
  }

  return (
    <div className="site-page cli-auth-page">
      <a className="site-skip-link" href="#auth-main">Skip to content</a>

      <SiteTopNav links={NAV_LINKS} />

      <main id="auth-main" className="site-main site-container cli-auth-main">
        <section className="site-card cli-auth-panel">
          <p className="site-label">Step 2 of 3</p>
          <h1 className="site-title">Sign in to continue in terminal</h1>
          <p className="site-text">
            Authenticate in browser, then return to your local CLI callback so terminal session can
            continue automatically.
          </p>

          {flow === 'device' && (
            <p className="site-text cli-auth-note">
              Device flow detected. After login, copy the redirected callback URL and paste it in
              the terminal prompt.
            </p>
          )}

          <div className="cli-auth-steps site-code-block">
            1. pip install devops-sentinel
            {'\n'}2. sentinel login
            {'\n'}3. Browser auth -&gt; back to CLI
          </div>

          <div className="site-btn-row">
            <a
              className="site-btn primary"
              href={emailAuthUrl}
              aria-disabled={!hasConfig}
            >
              Continue with email
            </a>
            <a
              className="site-btn secondary"
              href={githubAuthUrl}
              aria-disabled={!hasConfig}
            >
              Continue with GitHub
            </a>
          </div>

          {!hasConfig && (
            <div className="cli-auth-warning">
              Missing auth context. Open this page from <code className="site-inline-code">sentinel login</code>{' '}
              so it includes <code className="site-inline-code">supabase_url</code> and{' '}
              <code className="site-inline-code">redirect_uri</code>.
            </div>
          )}
        </section>

        <aside className="site-card soft cli-auth-terminal">
          <h2>Terminal fallback</h2>
          <pre className="site-code-block">
{`$ sentinel login
$ sentinel services add my-api https://api.example.com/health
$ sentinel monitor https://api.example.com/health`}
          </pre>
          <p className="site-text">If browser callback is blocked, use device flow:</p>
          <button className="site-btn secondary cli-auth-copy-btn" onClick={copyDeviceCommand}>
            {copied ? 'Copied' : 'Copy: sentinel login --device'}
          </button>
          <span className="sr-only" aria-live="polite">
            {copied ? 'Device login command copied.' : ''}
          </span>
        </aside>
      </main>

      <SiteFooter links={FOOTER_LINKS} text="DevOps Sentinel auth" />
    </div>
  )
}
