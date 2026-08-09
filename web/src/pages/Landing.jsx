import { useState } from 'react'
import { Link } from 'react-router-dom'
import SiteTopNav from '../components/site/SiteTopNav'
import SiteFooter from '../components/site/SiteFooter'
import './Landing.css'

const NAV_LINKS = [
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

const TERMINAL_BANNER = String.raw`╔══════════════════════════════════════════════════════════════════════╗
║                         DEVOPS SENTINEL                             ║
╚══════════════════════════════════════════════════════════════════════╝`

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
        <section className="landing-hero" aria-labelledby="landing-title">
          <p className="site-label">CLI-first incident response</p>
          <h1 id="landing-title" className="site-title">
            Monitor <span className="landing-diamond" aria-hidden="true">◆</span> detect &amp; resolve with AI
          </h1>
          <p className="site-text landing-intro">
            Autonomous SRE agents that watch your services, analyze incidents, and generate
            postmortems—all from your terminal.
          </p>

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

          <div className="landing-actions">
            <Link to="/cli-auth" className="landing-text-link">Get started <span aria-hidden="true">→</span></Link>
            <Link to="/operator/services" className="landing-text-link muted">Open operator console <span aria-hidden="true">→</span></Link>
          </div>
        </section>

        <section className="site-card soft landing-terminal-preview" aria-label="Sample terminal output">
          <div className="landing-terminal-header">
            <span className="landing-dot" />
            <span>devops-sentinel@terminal</span>
          </div>
          <pre className="landing-terminal-content">
{`${TERMINAL_BANNER}

$ sentinel monitor https://api.example.com/health
[PASS] /health 200 in 94ms
[PASS] /ready 200 in 88ms
[WARN] latency p95 above threshold
[INFO] run: sentinel incidents list`}
          </pre>
        </section>

        <section className="landing-steps-grid" aria-label="Getting started steps">
          <article className="site-card landing-step-card">
            <span className="landing-step-number">01</span>
            <h2>Install</h2>
            <p className="site-text">Install from PyPI and run the CLI locally.</p>
            <code className="site-inline-code">pip install devops-sentinel</code>
          </article>
          <article className="site-card landing-step-card">
            <span className="landing-step-number">02</span>
            <h2>Sign in</h2>
            <p className="site-text">Run login in terminal and complete auth on website.</p>
            <code className="site-inline-code">sentinel login</code>
          </article>
          <article className="site-card landing-step-card">
            <span className="landing-step-number">03</span>
            <h2>Monitor</h2>
            <p className="site-text">Add service URLs and start continuous health checks.</p>
            <code className="site-inline-code">sentinel monitor &lt;health-url&gt;</code>
          </article>
        </section>
      </main>

      <SiteFooter links={FOOTER_LINKS} text="DevOps Sentinel" />
    </div>
  )
}
