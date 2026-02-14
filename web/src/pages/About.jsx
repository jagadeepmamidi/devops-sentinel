import SiteTopNav from '../components/site/SiteTopNav'
import SiteFooter from '../components/site/SiteFooter'
import './About.css'

const NAV_LINKS = [
  { to: '/docs', label: 'Docs' },
  {
    href: 'https://github.com/jagadeepmamidi/devops-sentinel',
    label: 'GitHub',
    external: true,
  },
]

const FOOTER_LINKS = [
  { to: '/privacy', label: 'Privacy' },
  { to: '/terms', label: 'Terms' },
  { to: '/docs', label: 'Docs' },
]

export default function About() {
  return (
    <div className="site-page about-page">
      <a className="site-skip-link" href="#about-main">Skip to content</a>

      <SiteTopNav links={NAV_LINKS} />

      <main id="about-main" className="site-main site-container about-main-wrap">
        <section className="site-card about-hero">
          <p className="site-label">About DevOps Sentinel</p>
          <h1 className="site-title">Built for reliable incident response from terminal</h1>
          <p className="site-text">
            DevOps Sentinel helps engineering teams monitor services, detect anomalies, and run
            consistent remediation workflows without leaving the CLI.
          </p>
          <div className="site-code-pill">
            <span className="dollar">$</span>
            <code>sentinel setup && sentinel monitor https://api.example.com/health</code>
          </div>
        </section>

        <section className="site-card about-section">
          <h2>Mission</h2>
          <p className="site-text">
            On-call should be structured, fast, and measurable. We focus on reducing noise,
            improving triage quality, and shortening time to resolution.
          </p>
        </section>

        <section className="site-card about-section">
          <h2>Core capabilities</h2>
          <ul className="about-list">
            <li>Real-time service health monitoring</li>
            <li>AI-assisted anomaly detection and triage</li>
            <li>Incident correlation across services and deployments</li>
            <li>Terminal-first runbooks and operational workflow</li>
            <li>Post-incident summaries and team learning loops</li>
          </ul>
        </section>

        <section className="site-card about-section">
          <h2>Technology</h2>
          <p className="site-text">Built with practical, production-ready tools:</p>
          <div className="about-tech-stack">
            <span className="about-tech-tag">Python</span>
            <span className="about-tech-tag">FastAPI</span>
            <span className="about-tech-tag">Supabase</span>
            <span className="about-tech-tag">React</span>
            <span className="about-tech-tag">OpenAI</span>
            <span className="about-tech-tag">PostgreSQL</span>
          </div>
        </section>

        <section className="site-card soft about-contact">
          <h2>Contact</h2>
          <p className="site-text">Questions, feedback, or contributions:</p>
          <a href="mailto:jagadeep.mamidi@gmail.com">jagadeep.mamidi@gmail.com</a>
        </section>
      </main>

      <SiteFooter links={FOOTER_LINKS} text="Copyright 2026 DevOps Sentinel" />
    </div>
  )
}
