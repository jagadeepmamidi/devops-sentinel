import { Link } from 'react-router-dom'
import { useState } from 'react'
import './Landing.css'

export default function Landing() {
    const [copied, setCopied] = useState(false)

    const copyCommand = () => {
        navigator.clipboard.writeText('pip install devops-sentinel')
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    return (
        <div className="landing">
            {/* Minimal Nav - Gemini CLI style */}
            <nav className="nav">
                <div className="nav-brand">
                    <span className="logo-icon">⬢</span>
                    <span className="logo-text">DevOps Sentinel</span>
                </div>
                <div className="nav-links">
                    <Link to="/docs">Docs</Link>
                    <a href="https://github.com" target="_blank" rel="noopener noreferrer">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                        </svg>
                    </a>
                </div>
            </nav>

            {/* Hero Section */}
            <section className="hero">
                <h1>
                    Monitor <span className="logo-inline">⬢</span> detect & resolve with AI
                </h1>
                <p className="hero-subtitle">
                    Autonomous SRE agents that watch your services, analyze incidents,
                    and generate postmortems—all from your terminal.
                </p>

                {/* Install Command Box */}
                <div className="install-box">
                    <span className="prompt">$</span>
                    <code>pip install devops-sentinel</code>
                    <button className="copy-btn" onClick={copyCommand} title="Copy">
                        {copied ? '✓' : '⧉'}
                    </button>
                </div>

                <div className="cta-section">
                    <Link to="/docs" className="more-options">
                        Get started →
                    </Link>
                </div>
            </section>

            {/* Terminal Demo - Transparent Glass Style */}
            <section className="demo-section">
                <div className="demo-terminal">
                    <div className="terminal-ascii">
                        <pre>{`
  ██████╗ ███████╗██╗   ██╗ ██████╗ ██████╗ ███████╗
  ██╔══██╗██╔════╝██║   ██║██╔═══██╗██╔══██╗██╔════╝
  ██║  ██║█████╗  ╚██╗ ██╔╝██║   ██║██████╔╝███████╗
  ██████╔╝███████╗ ╚████╔╝ ╚██████╔╝██║     ╚════██║
  ╚═════╝ ╚══════╝  ╚═══╝   ╚═════╝ ╚═╝     ╚═════╝
  ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗     
  ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║     
  ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║     
  ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║     
  ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗
  ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝
        `}</pre>
                    </div>
                    <div className="terminal-tips">
                        <p><strong>Tips for getting started:</strong></p>
                        <p>1. Monitor any health endpoint with <code>sentinel monitor &lt;url&gt;</code></p>
                        <p>2. Get instant Slack alerts on incidents</p>
                        <p>3. View AI-generated postmortems with <code>sentinel postmortem</code></p>
                        <p>4. <code>/help</code> for more information.</p>
                    </div>
                    <div className="terminal-input">
                        <span className="prompt-arrow">&gt;</span>
                        <span className="input-placeholder">Ask Sentinel to monitor your API...</span>
                    </div>
                    <div className="terminal-status">
                        <span>~/my-project</span>
                        <span>sentinel-agent (active)</span>
                        <span>crew-ai</span>
                    </div>
                </div>
            </section>

            {/* Footer */}
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
