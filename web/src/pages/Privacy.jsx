import { Link } from 'react-router-dom'
import './Legal.css'

export default function Privacy() {
    return (
        <div className="legal-page">
            <nav className="legal-nav">
                <Link to="/" className="legal-nav-brand">
                    <span>⬢</span>
                    <span>DevOps Sentinel</span>
                </Link>
            </nav>

            <div className="legal-content">
                <h1>Privacy Policy</h1>
                <p className="last-updated">Last updated: January 28, 2026</p>

                <div className="legal-toc">
                    <h3>Contents</h3>
                    <ul>
                        <li><a href="#information">Information We Collect</a></li>
                        <li><a href="#usage">How We Use Your Information</a></li>
                        <li><a href="#sharing">Information Sharing</a></li>
                        <li><a href="#security">Data Security</a></li>
                        <li><a href="#rights">Your Rights</a></li>
                        <li><a href="#contact">Contact Us</a></li>
                    </ul>
                </div>

                <h2 id="information">Information We Collect</h2>
                <p>
                    DevOps Sentinel collects information necessary to provide our service monitoring
                    and incident management capabilities:
                </p>
                <ul>
                    <li>Account information (email address, name)</li>
                    <li>Service URLs and health check configurations</li>
                    <li>Incident data and postmortem reports</li>
                    <li>Usage analytics to improve our service</li>
                </ul>

                <h2 id="usage">How We Use Your Information</h2>
                <p>We use your information to:</p>
                <ul>
                    <li>Provide and maintain our monitoring service</li>
                    <li>Send alerts and notifications about your services</li>
                    <li>Generate AI-powered postmortems and insights</li>
                    <li>Improve and optimize our platform</li>
                    <li>Communicate important updates</li>
                </ul>

                <h2 id="sharing">Information Sharing</h2>
                <p>
                    We do not sell your personal information. We may share data with:
                </p>
                <ul>
                    <li>Service providers who assist in operating our platform (Supabase, OpenAI)</li>
                    <li>Law enforcement when required by law</li>
                    <li>Third parties with your explicit consent</li>
                </ul>

                <h2 id="security">Data Security</h2>
                <p>
                    We implement industry-standard security measures including encryption
                    in transit and at rest, regular security audits, and access controls.
                    Your credentials are stored securely and never logged in plain text.
                </p>

                <h2 id="rights">Your Rights</h2>
                <p>You have the right to:</p>
                <ul>
                    <li>Access your personal data</li>
                    <li>Request data deletion</li>
                    <li>Export your data</li>
                    <li>Opt out of marketing communications</li>
                </ul>

                <h2 id="contact">Contact Us</h2>
                <p>
                    For privacy-related questions, contact us at{' '}
                    <a href="mailto:privacy@devops-sentinel.dev">privacy@devops-sentinel.dev</a>
                </p>
            </div>

            <footer className="legal-footer">
                <div>
                    <Link to="/about">About</Link>
                    <Link to="/terms">Terms</Link>
                    <Link to="/docs">Docs</Link>
                </div>
            </footer>
        </div>
    )
}
