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
            <p className="site-label">CLI-first incident response</p>
            <h1 className="site-title">
              Monitor, detect, and resolve incidents from your terminal
            </h1>
            <p className="site-text">
              Install from PyPI, authenticate once in browser, then return to your terminal and
              start monitoring production services in minutes.
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

            <div className="site-btn-row">
              <Link to="/cli-auth" className="site-btn primary">Start CLI Login</Link>
              <Link to="/docs" className="site-btn secondary">Read Docs</Link>
            </div>
          </div>

          <div className="site-card soft landing-terminal-preview">
            <div className="landing-terminal-header">
              <span className="landing-dot" />
              <span>sentinel.live</span>
            </div>
            <pre className="landing-terminal-content" aria-label="Sample terminal output">
{`$ sentinel monitor https://api.example.com/health
[PASS] /health 200 in 94ms
[PASS] /ready 200 in 88ms
[WARN] latency p95 above threshold
[INFO] run: sentinel incidents list`}
            </pre>
          </div>
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
