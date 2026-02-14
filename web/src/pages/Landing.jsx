import { Link } from 'react-router-dom'
import { useState } from 'react'
import './Landing.css'

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
    <div className="landing">
      <a className="skip-link" href="#main-content">Skip to content</a>
      <nav className="nav">
        <div className="nav-brand">
          <span className="logo-icon">S</span>
          <span className="logo-text">DevOps Sentinel</span>
        </div>
        <div className="nav-links">
          <Link to="/cli-auth">CLI Login</Link>
          <Link to="/docs">Docs</Link>
          <a
            href="https://github.com/jagadeepmamidi/devops-sentinel"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="GitHub repository"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M12 0C5.37 0 0 5.37 0 12a12 12 0 0 0 8.2 11.39c.6.11.8-.26.8-.58v-2.2c-3.33.72-4.03-1.42-4.03-1.42-.54-1.38-1.33-1.75-1.33-1.75-1.1-.75.08-.73.08-.73 1.2.08 1.84 1.23 1.84 1.23 1.07 1.83 2.8 1.3 3.49 1 .1-.78.42-1.31.76-1.61-2.67-.3-5.47-1.33-5.47-5.93 0-1.3.47-2.38 1.24-3.22-.12-.3-.54-1.52.12-3.17 0 0 1-.32 3.3 1.23A11.5 11.5 0 0 1 12 5.8c1.02.01 2.04.14 3 .4 2.29-1.55 3.3-1.23 3.3-1.23.65 1.65.24 2.87.12 3.17.77.84 1.24 1.92 1.24 3.22 0 4.61-2.81 5.62-5.48 5.92.43.37.82 1.1.82 2.22v3.29c0 .32.19.7.8.58A12 12 0 0 0 24 12c0-6.63-5.37-12-12-12Z" />
            </svg>
          </a>
        </div>
      </nav>

      <main id="main-content" className="landing-main">
        <section className="hero">
          <div className="hero-copy">
            <p className="hero-label">CLI-first incident response</p>
            <h1>
              Operate incidents from a terminal-native
              <span className="headline-accent"> control surface</span>
            </h1>
            <p className="hero-subtitle">
              Install from PyPI, authenticate on web once, then run live health checks and guided
              remediation from your shell with fast, readable output.
            </p>

            <div className="install-box">
              <span className="prompt">$</span>
              <code>pip install devops-sentinel</code>
              <button
                className="copy-btn"
                onClick={copyCommand}
                title="Copy install command"
                aria-label="Copy install command"
              >
                {copied ? 'COPIED' : 'COPY'}
              </button>
              <span className="sr-only" aria-live="polite">
                {copied ? 'Install command copied.' : ''}
              </span>
            </div>

            <div className="cta-section">
              <Link to="/cli-auth" className="primary-cta">Start CLI Login</Link>
              <Link to="/docs" className="more-options">Read Docs</Link>
            </div>

            <ul className="command-rail">
              <li><span>sentinel setup</span><em>onboarding</em></li>
              <li><span>sentinel login</span><em>auth bridge</em></li>
              <li><span>sentinel monitor &lt;url&gt;</span><em>live checks</em></li>
            </ul>
          </div>

          <div className="hero-visual">
            <div className="scene-card">
              <div className="scene-titlebar">
                <span className="dot red" />
                <span className="dot yellow" />
                <span className="dot green" />
                <span>sentinel.live</span>
              </div>
              <pre className="ascii-art" aria-hidden="true">{`+---------------------------+
| D E V O P S  S E N T I N E L |
+---------------------------+
| status      : ACTIVE      |
| checks/min  : 48          |
| mttd        : 22s         |
| alerts(open): 01          |
+---------------------------+
|> sentinel monitor api     |
|  PASS  /health            |
|  PASS  /ready             |
|  WARN  latency p95 410ms  |
+---------------------------+`}</pre>
              <div className="scene-glow" aria-hidden="true" />
            </div>
            <div className="floating-chip">web auth linked</div>
            <div className="floating-chip chip-alt">agent online</div>
          </div>
        </section>

        <section className="flow-section">
          <div className="flow-card">
            <h3>1. Install</h3>
            <p>Install from PyPI and run the CLI locally.</p>
            <code>pip install devops-sentinel</code>
          </div>
          <div className="flow-card">
            <h3>2. Sign In</h3>
            <p>Run login in terminal and complete auth on website.</p>
            <code>sentinel login</code>
          </div>
          <div className="flow-card">
            <h3>3. Monitor</h3>
            <p>Add service URLs and monitor continuously with alert-ready output.</p>
            <code>sentinel monitor &lt;health-url&gt;</code>
          </div>
        </section>

        <section className="demo-section">
          <div className="demo-terminal">
            <div className="terminal-header">
              <strong>Starter commands</strong>
              <span>session: prod-eu-1</span>
            </div>
            <div className="terminal-log" aria-label="Sample terminal output">
              <p><span className="log-pass">PASS</span> https://api.example.com/health</p>
              <p><span className="log-pass">PASS</span> https://api.example.com/ready</p>
              <p><span className="log-warn">WARN</span> latency p95 exceeded threshold</p>
              <p><span className="log-info">INFO</span> opening guided incident flow</p>
            </div>
            <div className="terminal-input">
              <span className="prompt-arrow">&gt;</span>
              <span className="input-placeholder">sentinel doctor --verbose</span>
            </div>
            <div className="terminal-status">
              <span>~/prod-api</span>
              <span>agent active</span>
              <span>python cli</span>
            </div>
          </div>
          <div className="quick-help-card">
            <h3>If browser login is blocked</h3>
            <p>Use device flow from terminal and paste the token.</p>
            <code>sentinel login --device</code>
            <p className="quick-help-note">Works on remote servers and SSH sessions.</p>
          </div>
        </section>
      </main>

      <footer className="footer">
        <span className="footer-brand">DevOps Sentinel</span>
        <div className="footer-links">
          <Link to="/terms">Terms</Link>
          <span className="divider">|</span>
          <Link to="/privacy">Privacy</Link>
        </div>
      </footer>
    </div>
  )
}
