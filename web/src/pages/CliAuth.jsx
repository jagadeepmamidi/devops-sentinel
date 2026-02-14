import { Link, useSearchParams } from 'react-router-dom'
import { useState } from 'react'
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

export default function CliAuth() {
  const [searchParams] = useSearchParams()
  const [copied, setCopied] = useState(false)

  const supabaseUrl =
    searchParams.get('supabase_url') ||
    import.meta.env.VITE_SUPABASE_URL ||
    ''

  const redirectUri =
    searchParams.get('redirect_uri') ||
    'http://localhost:54321/callback'
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
    <div className="cli-auth-page">
      <a className="skip-link" href="#auth-main">Skip to content</a>
      <div className="mesh-bg" />
      <main id="auth-main" className="cli-auth-shell">
        <header className="cli-auth-header">
          <Link to="/" className="brand">
            <span className="brand-dot">S</span>
            <span>DevOps Sentinel</span>
          </Link>
          <span className="flow-tag">CLI auth flow</span>
        </header>

        <section className="hero-card">
          <p className="eyebrow">Step 2 of 3</p>
          <h1>Sign in to continue in terminal</h1>
          <p className="subtext">
            Sign in or create an account. After auth completes, this page redirects back to
            your local CLI callback and your terminal session continues.
          </p>
          {flow === 'device' && (
            <p className="auth-note">
              Device flow: after login, copy the full redirected callback URL from your browser
              and paste it in the terminal prompt.
            </p>
          )}

          <div className="flow-steps">
            <div>1. `pip install devops-sentinel`</div>
            <div>2. `sentinel login`</div>
            <div>3. Browser auth -&gt; back to CLI</div>
          </div>

          <div className="auth-actions">
            <a
              className={`action primary ${!hasConfig ? 'disabled' : ''}`}
              href={emailAuthUrl}
              aria-disabled={!hasConfig}
            >
              Continue with email
            </a>
            <a
              className={`action secondary ${!hasConfig ? 'disabled' : ''}`}
              href={githubAuthUrl}
              aria-disabled={!hasConfig}
            >
              Continue with GitHub
            </a>
          </div>

          <p className="auth-note">
            New users can sign up from either auth option above.
          </p>

          {!hasConfig && (
            <div className="warning">
              Missing auth context. Open this page from `sentinel login` so it includes
              `supabase_url` and `redirect_uri`.
            </div>
          )}
        </section>

        <section className="terminal-card">
          <p className="terminal-title">In your terminal</p>
          <pre>
{`$ sentinel login
$ sentinel services add "my-api" https://api.example.com/health
$ sentinel monitor https://api.example.com/health`}
          </pre>
          <div className="device-fallback">
            <p>Browser blocked or running over SSH?</p>
            <button className="copy-device-btn" onClick={copyDeviceCommand}>
              {copied ? 'Copied' : 'Copy: sentinel login --device'}
            </button>
            <span className="sr-only" aria-live="polite">
              {copied ? 'Device login command copied.' : ''}
            </span>
          </div>
        </section>
      </main>
    </div>
  )
}
