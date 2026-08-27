import { useState } from 'react'
import { Link } from 'react-router-dom'
import OrbitalScene from '../components/site/OrbitalScene'
import SiteTopNav from '../components/site/SiteTopNav'
import SiteFooter from '../components/site/SiteFooter'
import './Landing.css'

const NAV_LINKS = [
  { to: '/about', label: 'Why Sentinel' },
  { to: '/docs', label: 'Docs' },
  {
    href: 'https://github.com/jagadeepmamidi/devops-sentinel',
    label: 'GitHub',
    external: true,
  },
  { to: '/cli-auth', label: 'Open Console', className: 'outline' },
]

const FOOTER_LINKS = [
  { to: '/about', label: 'About' },
  { to: '/docs', label: 'Docs' },
  { to: '/terms', label: 'Terms' },
  { to: '/privacy', label: 'Privacy' },
]

const healthRows = [
  { name: 'api-gateway', url: '/health', latency: '84 ms', status: 'Nominal', width: '88%' },
  { name: 'checkout-worker', url: '/ready', latency: '112 ms', status: 'Nominal', width: '72%' },
  { name: 'edge-cache', url: '/ping', latency: '96 ms', status: 'Watching', width: '80%' },
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
          <div className="landing-hero-copy">
            <div className="landing-eyebrow">
              <span className="landing-eyebrow-dot" />
              Autonomous SRE intelligence / v0.2
            </div>
            <h1 className="landing-headline">
              See every signal <span>before</span> it becomes an incident.
            </h1>
            <p className="landing-lede">
              DevOps Sentinel watches the systems that matter, turns noisy telemetry into a clear
              operational picture, and gives your team the next move from the terminal.
            </p>

            <div className="site-btn-row landing-hero-actions">
              <Link to="/cli-auth" className="site-btn primary">Start monitoring <span>↗</span></Link>
              <Link to="/docs" className="site-btn secondary">Explore the workflow</Link>
            </div>

            <div className="landing-install-row">
              <div className="landing-install-pill" role="group" aria-label="Install command">
                <span className="landing-command-prompt">$</span>
                <code>pip install devops-sentinel</code>
                <button className="landing-copy-btn" onClick={copyCommand} type="button">
                  {copied ? 'Copied' : 'Copy'}
                </button>
              </div>
              <span className="landing-install-note">Python · open source · local-first</span>
            </div>
            <span className="sr-only" aria-live="polite">
              {copied ? 'Install command copied.' : ''}
            </span>
          </div>

          <div className="landing-hero-visual site-card" aria-label="Live monitoring visualization">
            <div className="landing-visual-header">
              <div>
                <span className="landing-overline">Sentinel mesh</span>
                <strong>Production / all systems</strong>
              </div>
              <span className="landing-live-pill"><span /> Live</span>
            </div>
            <OrbitalScene />
            <div className="landing-visual-readout landing-visual-readout-top">
              <span>Signal integrity</span><strong>99.98%</strong>
            </div>
            <div className="landing-visual-readout landing-visual-readout-bottom">
              <span>Last pulse</span><strong>00:00:04</strong>
            </div>
            <div className="landing-orbit-caption"><span>◉</span> 12 services · 3 regions · 0 open incidents</div>
          </div>
        </section>

        <section className="landing-signal-bar" aria-label="Current system signal">
          <div className="landing-signal-main">
            <span className="landing-signal-icon">↗</span>
            <div><span className="landing-overline">Current signal</span><strong>All monitored surfaces are nominal</strong></div>
          </div>
          <div className="landing-signal-meta"><span>Last scan</span><strong>4 sec ago</strong><i /><span>Next scan</span><strong>26 sec</strong></div>
        </section>

        <section className="landing-section-heading">
          <div>
            <span className="landing-overline">From noise to signal</span>
            <h2>An operational cockpit that stays out of the way.</h2>
          </div>
          <p>One clean loop for the moments that matter: observe, understand, respond, learn.</p>
        </section>

        <section className="landing-system-grid">
          <article className="site-card landing-health-card">
            <div className="landing-card-heading">
              <div><span className="landing-overline">Live surface map</span><h3>Service health</h3></div>
              <span className="landing-card-count">03 / 03</span>
            </div>
            <div className="landing-health-list">
              {healthRows.map((row) => (
                <div className="landing-health-row" key={row.name}>
                  <div className="landing-health-name"><span className="landing-health-dot" /><strong>{row.name}</strong><code>{row.url}</code></div>
                  <div className="landing-health-bar"><span style={{ width: row.width }} /></div>
                  <span className={`landing-health-status ${row.status === 'Watching' ? 'watching' : ''}`}>{row.status}</span>
                  <span className="landing-health-latency">{row.latency}</span>
                </div>
              ))}
            </div>
            <div className="landing-health-footer"><span><i /> Response time / last 24h</span><Link to="/docs">View runbook →</Link></div>
          </article>

          <aside className="site-card landing-loop-card">
            <span className="landing-overline">The Sentinel loop</span>
            <h3>Move from alert to action with context intact.</h3>
            <div className="landing-loop-list">
              <div className="landing-loop-item"><span>01</span><div><strong>Observe</strong><p>Continuous checks across every endpoint.</p></div></div>
              <div className="landing-loop-item"><span>02</span><div><strong>Understand</strong><p>Anomalies become concise incident context.</p></div></div>
              <div className="landing-loop-item"><span>03</span><div><strong>Respond</strong><p>Runbooks and next steps at your fingertips.</p></div></div>
            </div>
          </aside>
        </section>

        <section className="landing-terminal-section">
          <div className="landing-terminal-copy">
            <span className="landing-overline">Terminal-native by design</span>
            <h2>Your best interface is already open.</h2>
            <p>Install once, authenticate in your browser, then keep your operational loop in the terminal you trust.</p>
            <Link to="/docs" className="landing-text-link">Read the quick start <span>→</span></Link>
          </div>
          <div className="landing-terminal-window">
            <div className="landing-terminal-topbar"><span className="landing-terminal-dots"><i /><i /><i /></span><span>sentinel / production</span><span className="landing-terminal-lock">⌘</span></div>
            <pre aria-label="Sample Sentinel terminal output"><span className="term-dim">$ sentinel setup</span>{'\n'}<span className="term-green">OK</span> local identity ready{ '\n' }<span className="term-green">OK</span> OpenRouter key stored securely{ '\n' }<span className="term-green">OK</span> monitoring <span className="term-blue">example.com</span>{'\n\n'}<span className="term-dim">$ sentinel status</span>{'\n'}<span className="term-green">●</span> all systems operational{ '\n' }<span className="term-dim">↳ next scan in 26s</span></pre>
          </div>
        </section>

        <section className="landing-cta site-card">
          <div><span className="landing-overline">Ready when you are</span><h2>Give your on-call a better signal.</h2></div>
          <div className="site-btn-row"><Link to="/cli-auth" className="site-btn primary">Open the console <span>↗</span></Link><Link to="/about" className="site-btn secondary">Meet the project</Link></div>
        </section>
      </main>

      <SiteFooter links={FOOTER_LINKS} text="DevOps Sentinel · Built for calm on-call" />
    </div>
  )
}
