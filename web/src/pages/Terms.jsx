import { Link } from 'react-router-dom'
import './Legal.css'

export default function Terms() {
    return (
        <div className="legal-page">
            <nav className="legal-nav">
                <Link to="/" className="legal-nav-brand">
                    <span>⬢</span>
                    <span>DevOps Sentinel</span>
                </Link>
            </nav>

            <div className="legal-content">
                <h1>Terms of Service</h1>
                <p className="last-updated">Last updated: January 28, 2026</p>

                <div className="legal-toc">
                    <h3>Contents</h3>
                    <ul>
                        <li><a href="#acceptance">Acceptance of Terms</a></li>
                        <li><a href="#service">Service Description</a></li>
                        <li><a href="#account">Your Account</a></li>
                        <li><a href="#usage">Acceptable Use</a></li>
                        <li><a href="#liability">Limitation of Liability</a></li>
                        <li><a href="#termination">Termination</a></li>
                    </ul>
                </div>

                <h2 id="acceptance">Acceptance of Terms</h2>
                <p>
                    By accessing or using DevOps Sentinel, you agree to be bound by these Terms
                    of Service. If you do not agree to these terms, do not use our service.
                </p>

                <h2 id="service">Service Description</h2>
                <p>
                    DevOps Sentinel provides service monitoring, incident management, and
                    AI-powered postmortem generation tools. We offer both free and paid tiers
                    with varying features and limits.
                </p>

                <h2 id="account">Your Account</h2>
                <p>You are responsible for:</p>
                <ul>
                    <li>Maintaining the security of your account credentials</li>
                    <li>All activities that occur under your account</li>
                    <li>Notifying us of any unauthorized access</li>
                    <li>Providing accurate account information</li>
                </ul>

                <h2 id="usage">Acceptable Use</h2>
                <p>You agree not to:</p>
                <ul>
                    <li>Use the service for any illegal purpose</li>
                    <li>Attempt to gain unauthorized access to our systems</li>
                    <li>Interfere with or disrupt the service</li>
                    <li>Use the service to monitor URLs without authorization</li>
                    <li>Exceed rate limits or abuse the platform</li>
                </ul>

                <h2 id="liability">Limitation of Liability</h2>
                <p>
                    DevOps Sentinel is provided "as is" without warranties of any kind.
                    We are not liable for any indirect, incidental, or consequential damages
                    arising from your use of the service. Our total liability is limited to
                    the amount you paid for the service in the past 12 months.
                </p>

                <h2 id="termination">Termination</h2>
                <p>
                    We may terminate or suspend your account at any time for violation of
                    these terms. You may terminate your account at any time by contacting us.
                    Upon termination, your data will be deleted within 30 days.
                </p>

                <h2>Changes to Terms</h2>
                <p>
                    We may update these terms from time to time. Continued use of the service
                    after changes constitutes acceptance of the new terms.
                </p>

                <h2>Contact</h2>
                <p>
                    For questions about these terms, contact us at{' '}
                    <a href="mailto:legal@devops-sentinel.dev">legal@devops-sentinel.dev</a>
                </p>
            </div>

            <footer className="legal-footer">
                <div>
                    <Link to="/about">About</Link>
                    <Link to="/privacy">Privacy</Link>
                    <Link to="/docs">Docs</Link>
                </div>
            </footer>
        </div>
    )
}
