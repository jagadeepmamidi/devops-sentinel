import { Link } from 'react-router-dom'
import './About.css'

export default function About() {
  return (
    <div className="about-page">
      <a className="about-skip-link" href="#about-main">Skip to content</a>
      <div className="about-grid-overlay" aria-hidden="true" />

      <nav className="about-nav">
        <Link to="/" className="about-nav-brand">
          <span className="about-brand-dot">S</span>
          <span>DevOps Sentinel</span>
        </Link>
        <div className="about-nav-links">
          <Link to="/docs">Docs</Link>
          <a
            href="https://github.com/jagadeepmamidi/devops-sentinel"
            target="_blank"
            rel="noopener noreferrer"
          >
            GitHub
          </a>
        </div>
      </nav>

      <main id="about-main" className="about-main">
        <header className="about-hero">
          <p className="about-eyebrow">About DevOps Sentinel</p>
          <h1>Built for operators who run incident response from the terminal</h1>
          <p className="about-subtitle">
            DevOps Sentinel is an autonomous SRE assistant that watches your services, detects
            anomalies, and helps teams respond with consistent workflows and actionable context.
          </p>
          <div className="about-command">
            <span>$</span>
            <code>sentinel setup && sentinel monitor https://api.example.com/health</code>
          </div>
        </header>

        <section className="about-section">
          <h2>Mission</h2>
          <p>
            On-call should not mean constant firefighting. DevOps Sentinel focuses on practical
            reliability workflows that reduce noise, shorten time to detection, and improve
            incident quality over time.
          </p>
        </section>

        <section className="about-section">
          <h2>What It Covers</h2>
          <ul className="about-list">
            <li>Real-time service health monitoring</li>
            <li>AI-assisted anomaly detection and triage</li>
            <li>Incident correlation across services and deployments</li>
            <li>Terminal-first runbooks and guided response flow</li>
            <li>Post-incident summaries for team learning</li>
            <li>CLI ergonomics for local and remote environments</li>
          </ul>
        </section>

        <section className="about-section">
          <h2>Technology</h2>
          <p>Built with practical, production-ready technologies:</p>
          <div className="about-tech-stack">
            <span className="about-tech-tag">Python</span>
            <span className="about-tech-tag">FastAPI</span>
            <span className="about-tech-tag">Supabase</span>
            <span className="about-tech-tag">React</span>
            <span className="about-tech-tag">OpenAI</span>
            <span className="about-tech-tag">PostgreSQL</span>
          </div>
        </section>

        <section className="about-section">
          <h2>Open Source</h2>
          <p>
            DevOps Sentinel is open source and community-driven. Clear docs, reproducible workflows,
            and collaborative iteration are part of the roadmap.
          </p>
        </section>

        <section className="about-contact">
          <h2>Get in Touch</h2>
          <p>Questions, feedback, or contributions:</p>
          <a href="mailto:jagadeep.mamidi@gmail.com">jagadeep.mamidi@gmail.com</a>
        </section>
      </main>

      <footer className="about-footer">
        <div className="about-footer-links">
          <Link to="/privacy">Privacy</Link>
          <Link to="/terms">Terms</Link>
          <Link to="/docs">Docs</Link>
        </div>
        <p>Copyright 2026 DevOps Sentinel. All rights reserved.</p>
      </footer>
    </div>
  )
}
