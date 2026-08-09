import { useState } from 'react'
import { Link } from 'react-router-dom'
import SiteTopNav from '../components/site/SiteTopNav'
import SiteFooter from '../components/site/SiteFooter'
import './Landing.css'

const NAV_LINKS = [
  { to: '/operator/services', label: 'Operator' },
  { to: '/cli-auth', label: 'CLI Login' },
  { to: '/docs', label: 'Docs' },
  {
    href: 'https://github.com/jagadeepmamidi/devops-sentinel',
    label: 'GitHub',
    external: true,
  },
]

const FOOTER_LINKS = [
  { to: '/terms', label: 'Terms' },
  { to: '/privacy', label: 'Privacy' },
]

export default function Landing() {
  const [copied, setCopied] = useState(false)

  const copyCommand = async () => {
    try {
      await navigator.clipboard.writeText('pip install devops-sentinel')
      setCopied(true)
      setTimeout(() => setCopied(false), 1800)
    } catch {
      setCopied(false)
    }
  }

  return (
    <div className="site-page landing-page">
      <a className="site-skip-link" href="#landing-main">Skip to content</a>

      <SiteTopNav links={NAV_LINKS} />

      <main id="landing-main" className="site-main site-container">
        <section className="landing-hero-grid">
          <div className="site-card landing-hero-card">
            <div className="landing-eyebrow">
              <span className="landing-eyebrow-dot" aria-hidden="true" />
              <span>CLI-first incident response</span>
              <span className="landing-eyebrow-status">v0.3 now available</span>
            </div>
            <h1 className="site-title">
              See the signal. <span>Fix the incident.</span>
            </h1>
            <p className="site-text">
              DevOps Sentinel gives your team one calm, actionable view of production health —
              from the first failing check to the final postmortem.
            </p>

            <div className="landing-proof-row" aria-label="Product capabilities">
              <span><strong>94ms</strong> sample check</span>
              <span><strong>24/7</strong> service coverage</span>
              <span><strong>1 CLI</strong> to operate</span>
            </div>

            <div className="landing-install-pill" role="group" aria-label="Install command">
              <span className="dollar">$</span>
              <code>pip install devops-sentinel</code>
              <button
                className="landing-copy-btn"
                onClick={copyCommand}
                title="Copy install command"
                aria-label="Copy install command"
              >
                {copied ? 'Copied' : 'Copy'}
              </button>
              <span className="sr-only" aria-live="polite">
                {copied ? 'Install command copied.' : ''}
              </span>
            </div>

            <div className="site-btn-row">
              <Link to="/operator/services" className="site-btn secondary">Open Operator Console</Link>
              <Link to="/cli-auth" className="site-btn primary">Start CLI Login</Link>
              <Link to="/docs" className="site-btn secondary">Read Docs</Link>
            </div>
          </div>

          <div className="site-card soft landing-terminal-preview">
            <div className="landing-terminal-header">
              <span className="landing-dot" />
              <span>devops-sentinel@terminal</span>
            </div>
            <pre className="landing-terminal-content" aria-label="Sample terminal output">
{` ____              ____               _____            _   _             _
|  _ \\  _____   __ / ___|  ___  _ __  |_   _|___   ___ | |_(_)_ __   __ _| |
| | | |/ _ \\ \\ / / \\___ \\ / _ \\| '_ \\   | |/ _ \\ / _ \\| __| | '_ \\ / _\` | |
| |_| |  __/\\ V /   ___) | (_) | | | |  | | (_) | (_) | |_| | | | | (_| | |
|____/ \\___| \\_/   |____/ \\___/|_| |_|  |_|\\___/ \\___/ \\__|_|_| |_|\\__,_|_|

$ sentinel monitor https://api.example.com/health
[PASS] /health 200 in 94ms
[PASS] /ready 200 in 88ms
[WARN] latency p95 above threshold
[INFO] run: sentinel incidents list`}
            </pre>
          </div>
        </section>

        <section className="landing-feature-grid" aria-label="What Sentinel does">
          <article className="landing-feature-card">
            <span className="landing-feature-index">01</span>
            <h2>Know what changed</h2>
            <p className="site-text">Correlate health signals with deployments before the alert becomes a guessing game.</p>
          </article>
          <article className="landing-feature-card">
            <span className="landing-feature-index">02</span>
            <h2>Move with context</h2>
            <p className="site-text">Get incident summaries, likely causes, and the next best action in one place.</p>
          </article>
          <article className="landing-feature-card">
            <span className="landing-feature-index">03</span>
            <h2>Learn after recovery</h2>
            <p className="site-text">Turn every outage into a searchable postmortem your team can actually use.</p>
          </article>
        </section>

        <section className="landing-steps-grid" aria-label="Getting started steps">
          <article className="site-card landing-step-card">
            <h2>1. Install</h2>
            <p className="site-text">Install from PyPI and run the CLI locally.</p>
            <code className="site-inline-code">pip install devops-sentinel</code>
          </article>
          <article className="site-card landing-step-card">
            <h2>2. Sign In</h2>
            <p className="site-text">Run login in terminal and complete auth on website.</p>
            <code className="site-inline-code">sentinel login</code>
          </article>
          <article className="site-card landing-step-card">
            <h2>3. Monitor</h2>
            <p className="site-text">Add service URLs and start continuous health checks.</p>
            <code className="site-inline-code">sentinel monitor &lt;health-url&gt;</code>
          </article>
        </section>

        <section className="landing-support-grid">
          <article className="site-card landing-commands-card">
            <h3>Starter commands</h3>
            <ul>
              <li><code className="site-inline-code">sentinel setup</code> for guided onboarding</li>
              <li><code className="site-inline-code">sentinel login</code> to connect account</li>
              <li><code className="site-inline-code">sentinel doctor</code> for diagnostics</li>
            </ul>
          </article>
          <article className="site-card soft landing-help-card">
            <h3>Browser login blocked?</h3>
            <p className="site-text">Use device flow from terminal and paste the callback token.</p>
            <code className="site-inline-code">sentinel login --device</code>
            <p className="site-text">Works in SSH and remote server environments.</p>
          </article>
        </section>
      </main>

      <SiteFooter links={FOOTER_LINKS} text="DevOps Sentinel" />
    </div>
  )
}
