import { Link } from 'react-router-dom'
import { useMemo, useState } from 'react'
import SiteTopNav from '../components/site/SiteTopNav'
import SiteFooter from '../components/site/SiteFooter'
import './Docs.css'

const NAV_LINKS = [
  { to: '/cli-auth', label: 'CLI Auth' },
  { to: '/feedback', label: 'Feedback', className: 'outline' },
]

const FOOTER_LINKS = [
  { to: '/terms', label: 'Terms' },
  { to: '/privacy', label: 'Privacy' },
  { to: '/about', label: 'About' },
]

const DOC_SECTIONS = {
  overview: {
    title: 'Overview',
    body: (
      <>
        <h2>What is DevOps Sentinel?</h2>
        <p>
          DevOps Sentinel is an AI-assisted SRE tool for CLI-first incident response. It helps
          teams detect, triage, and resolve service issues with practical workflows.
        </p>
        <div className="docs-feature-grid">
          <article className="site-card soft docs-feature-card">
            <h3>Intelligent monitoring</h3>
            <p>Detect availability and latency anomalies before they escalate.</p>
          </article>
          <article className="site-card soft docs-feature-card">
            <h3>Actionable incident context</h3>
            <p>Get concise, operator-friendly summaries and next-step guidance.</p>
          </article>
          <article className="site-card soft docs-feature-card">
            <h3>CLI-first workflow</h3>
            <p>Install, authenticate, and operate from terminal with minimal overhead.</p>
          </article>
        </div>
      </>
    ),
  },
  quickstart: {
    title: 'Quick Start',
    body: (
      <>
        <h2>Install and run in minutes</h2>
        <div className="docs-steps">
          <article className="site-card docs-step">
            <h3>1. Install</h3>
            <div className="site-code-block">pip install devops-sentinel</div>
          </article>
          <article className="site-card docs-step">
            <h3>2. Login</h3>
            <div className="site-code-block">sentinel login</div>
          </article>
          <article className="site-card docs-step">
            <h3>3. Monitor</h3>
            <div className="site-code-block">sentinel monitor https://api.example.com/health</div>
          </article>
        </div>
      </>
    ),
  },
  commands: {
    title: 'Commands',
    body: (
      <>
        <h2>Core CLI commands</h2>
        <div className="docs-command-list">
          <article className="site-card soft docs-command-item">
            <h3>Setup</h3>
            <p>Guided onboarding and local environment validation.</p>
            <code className="site-inline-code">sentinel setup</code>
          </article>
          <article className="site-card soft docs-command-item">
            <h3>Doctor</h3>
            <p>Check network, auth, and dependency health for troubleshooting.</p>
            <code className="site-inline-code">sentinel doctor</code>
          </article>
          <article className="site-card soft docs-command-item">
            <h3>Incidents</h3>
            <p>Inspect and manage incident records from terminal.</p>
            <code className="site-inline-code">sentinel incidents list</code>
          </article>
        </div>
      </>
    ),
  },
  api: {
    title: 'API',
    body: (
      <>
        <h2>Programmatic access</h2>
        <p>Use the REST API when integrating monitoring into your automation pipelines.</p>
        <div className="site-code-block">
          curl -H "Authorization: Bearer YOUR_API_KEY" \
          {'\n'}  https://api.devops-sentinel.dev/v1/services
        </div>
        <div className="docs-endpoints">
          <div className="site-card soft docs-endpoint">
            <span className="docs-method get">GET</span>
            <span>/v1/services</span>
          </div>
          <div className="site-card soft docs-endpoint">
            <span className="docs-method post">POST</span>
            <span>/v1/incidents</span>
          </div>
        </div>
      </>
    ),
  },
  faq: {
    title: 'FAQ',
    body: (
      <>
        <h2>Frequently asked questions</h2>
        <article className="site-card soft docs-faq-item">
          <h3>What data is collected?</h3>
          <p>
            Service health metrics, incident records, and usage analytics needed to operate the
            platform. See <Link to="/privacy">Privacy Policy</Link>.
          </p>
        </article>
        <article className="site-card soft docs-faq-item">
          <h3>Can I use this in SSH sessions?</h3>
          <p>
            Yes. Use <code className="site-inline-code">sentinel login --device</code> when browser
            callback flow is not available.
          </p>
        </article>
      </>
    ),
  },
}

export default function Docs() {
  const [activeSection, setActiveSection] = useState('overview')
  const section = useMemo(() => DOC_SECTIONS[activeSection], [activeSection])

  return (
    <div className="site-page docs-page">
      <a className="site-skip-link" href="#docs-main">Skip to content</a>

      <SiteTopNav links={NAV_LINKS} />

      <main className="site-main site-container docs-main-wrap">
        <section className="site-card docs-hero">
          <p className="site-label">Documentation</p>
          <h1 className="site-title">Operator guide for CLI-first incident response</h1>
          <p className="site-text">
            Follow a consistent production workflow: install package, authenticate once, monitor
            continuously, and respond faster from terminal.
          </p>
          <div className="site-code-pill">
            <span className="dollar">$</span>
            <code>sentinel login && sentinel monitor &lt;health-url&gt;</code>
          </div>
        </section>

        <section className="docs-layout">
          <aside className="site-card docs-sidebar" aria-label="Documentation sections">
            {Object.entries(DOC_SECTIONS).map(([key, value]) => (
              <button
                key={key}
                type="button"
                className={`docs-nav-btn ${activeSection === key ? 'active' : ''}`}
                onClick={() => setActiveSection(key)}
              >
                {value.title}
              </button>
            ))}
          </aside>

          <article id="docs-main" className="site-card docs-content">
            {section.body}
          </article>
        </section>
      </main>

      <SiteFooter links={FOOTER_LINKS} text="DevOps Sentinel docs" />
    </div>
  )
}
