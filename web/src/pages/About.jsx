import { Link } from 'react-router-dom'
import './About.css'

export default function About() {
    return (
        <div className="about-page">
            <nav className="about-nav">
                <Link to="/" className="about-nav-brand">
                    <span>⬢</span>
                    <span>DevOps Sentinel</span>
                </Link>
            </nav>

            <div className="about-content">
                <h1>About</h1>
                <p className="subtitle">
                    DevOps Sentinel is an autonomous SRE agent that watches your services,
                    detects anomalies, and generates blameless postmortems — all from your terminal.
                </p>

                <section className="about-section">
                    <h2>Our Mission</h2>
                    <p>
                        We believe on-call shouldn't mean sleepless nights. DevOps Sentinel
                        provides intelligent monitoring that learns from your infrastructure,
                        correlates incidents with deployments, and helps you build more
                        reliable systems.
                    </p>
                </section>

                <section className="about-section">
                    <h2>What We Do</h2>
                    <ul>
                        <li>Real-time service health monitoring</li>
                        <li>AI-powered anomaly detection</li>
                        <li>Automatic incident correlation</li>
                        <li>Blameless postmortem generation</li>
                        <li>Smart alerting with context</li>
                        <li>CLI-first developer experience</li>
                    </ul>
                </section>

                <section className="about-section">
                    <h2>Technology</h2>
                    <p>Built with modern, battle-tested technologies:</p>
                    <div className="tech-stack">
                        <span className="tech-tag">Python</span>
                        <span className="tech-tag">FastAPI</span>
                        <span className="tech-tag">Supabase</span>
                        <span className="tech-tag">React</span>
                        <span className="tech-tag">OpenAI</span>
                        <span className="tech-tag">PostgreSQL</span>
                    </div>
                </section>

                <section className="about-section">
                    <h2>Open Source</h2>
                    <p>
                        DevOps Sentinel is open source. We believe in transparency and
                        community-driven development. Contributions are welcome.
                    </p>
                </section>

                <div className="contact-section">
                    <h2>Get in Touch</h2>
                    <p>Questions, feedback, or want to contribute?</p>
                    <a href="mailto:jagadeep.mamidi@gmail.com">jagadeep.mamidi@gmail.com</a>
                </div>
            </div>

            <footer className="about-footer">
                <div>
                    <Link to="/privacy">Privacy</Link>
                    <Link to="/terms">Terms</Link>
                    <Link to="/docs">Docs</Link>
                </div>
                <p style={{ marginTop: '16px' }}>© 2026 DevOps Sentinel. All rights reserved.</p>
            </footer>
        </div>
    )
}
