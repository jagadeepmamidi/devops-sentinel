import { Link } from 'react-router-dom'
import { useState } from 'react'
import './Docs.css'

export default function Docs() {
    const [activeSection, setActiveSection] = useState('overview')

    const sections = {
        overview: {
            title: 'Overview',
            content: (
                <>
                    <h2>What is DevOps Sentinel?</h2>
                    <p>
                        DevOps Sentinel is an AI-powered SRE monitoring platform that helps teams detect,
                        diagnose, and resolve incidents faster. Think of it as your 24/7 DevOps co-pilot.
                    </p>

                    <h3>Key Features</h3>
                    <div className="feature-grid">
                        <div className="feature-card">
                            <h4>Intelligent Monitoring</h4>
                            <p>ML-powered anomaly detection catches issues before they become incidents</p>
                        </div>
                        <div className="feature-card">
                            <h4>AI Analysis</h4>
                            <p>Automatic postmortems and root cause analysis powered by advanced AI</p>
                        </div>
                        <div className="feature-card">
                            <h4>Smart Alerting</h4>
                            <p>Context-aware alerts with severity-based routing and escalation</p>
                        </div>
                        <div className="feature-card">
                            <h4>Dependency Mapping</h4>
                            <p>Visualize service dependencies and predict cascade failures</p>
                        </div>
                        <div className="feature-card">
                            <h4>Deployment Tracking</h4>
                            <p>Correlate incidents with deployments and suggest rollbacks</p>
                        </div>
                        <div className="feature-card">
                            <h4>Team Collaboration</h4>
                            <p>Slack integration, on-call schedules, and incident timelines</p>
                        </div>
                    </div>
                </>
            )
        },
        quickstart: {
            title: 'Quick Start',
            content: (
                <>
                    <h2>Get Started in 5 Minutes</h2>

                    <div className="step-card">
                        <div className="step-number">1</div>
                        <div className="step-content">
                            <h3>Create an Account</h3>
                            <p>Sign up with your email and create your organization</p>
                            <div className="code-block">
                                <code>https://devops-sentinel.dev/signup</code>
                            </div>
                        </div>
                    </div>

                    <div className="step-card">
                        <div className="step-number">2</div>
                        <div className="step-content">
                            <h3>Add Your First Service</h3>
                            <p>Configure a service to monitor (API, website, database, etc.)</p>
                            <div className="code-block">
                                <code>
                                    Service Name: My API<br />
                                    URL: https://api.example.com/health<br />
                                    Check Interval: 60 seconds
                                </code>
                            </div>
                        </div>
                    </div>

                    <div className="step-card">
                        <div className="step-number">3</div>
                        <div className="step-content">
                            <h3>Configure Alerts</h3>
                            <p>Set up notifications via Slack, email, or PagerDuty</p>
                            <div className="code-block">
                                <code>Settings → Integrations → Connect Slack</code>
                            </div>
                        </div>
                    </div>

                    <div className="step-card">
                        <div className="step-number">4</div>
                        <div className="step-content">
                            <h3>You're Live!</h3>
                            <p>DevOps Sentinel is now monitoring your services 24/7</p>
                        </div>
                    </div>
                </>
            )
        },
        features: {
            title: 'Features',
            content: (
                <>
                    <h2>Core Features</h2>

                    <div className="feature-detail">
                        <h3>Failure Classification</h3>
                        <p>
                            Intelligent incident detection with confidence scoring to prevent alert fatigue.
                            Automatically classifies failures by severity (P0-P3).
                        </p>
                    </div>

                    <div className="feature-detail">
                        <h3>Incident Memory</h3>
                        <p>
                            AI-powered similarity search finds similar past incidents and suggests proven remediation steps.
                        </p>
                    </div>

                    <div className="feature-detail">
                        <h3>Dependency Analysis</h3>
                        <p>
                            Build service dependency graphs to calculate blast radius and predict cascade failures.
                        </p>
                    </div>

                    <div className="feature-detail">
                        <h3>ML Anomaly Detection</h3>
                        <p>
                            Machine learning detects anomalies in response times, error rates, and traffic patterns.
                        </p>
                    </div>

                    <div className="feature-detail">
                        <h3>On-Call Management</h3>
                        <p>
                            Schedule rotations with weekly/daily shifts, overrides, and multi-level escalation.
                        </p>
                    </div>

                    <div className="feature-detail">
                        <h3>Deployment Correlation</h3>
                        <p>
                            Track deployments and correlate with incidents to suggest rollbacks.
                        </p>
                    </div>
                </>
            )
        },
        api: {
            title: 'API Reference',
            content: (
                <>
                    <h2>API Documentation</h2>
                    <p>Access DevOps Sentinel programmatically via REST API</p>

                    <h3>Authentication</h3>
                    <div className="code-block">
                        <code>
                            curl -H "Authorization: Bearer YOUR_API_KEY" \<br />
                            &nbsp;&nbsp;https://api.devops-sentinel.dev/v1/services
                        </code>
                    </div>

                    <h3>Endpoints</h3>

                    <div className="api-endpoint">
                        <div className="api-method get">GET</div>
                        <div className="api-path">/v1/services</div>
                        <p>List all monitored services</p>
                    </div>

                    <div className="api-endpoint">
                        <div className="api-method post">POST</div>
                        <div className="api-path">/v1/incidents</div>
                        <p>Create incident</p>
                    </div>
                </>
            )
        },
        integrations: {
            title: 'Integrations',
            content: (
                <>
                    <h2>Connect Your Tools</h2>

                    <div className="integration-card">
                        <div className="integration-content">
                            <h3>Slack</h3>
                            <p>Get incident alerts in Slack with threaded updates</p>
                        </div>
                    </div>

                    <div className="integration-card">
                        <div className="integration-content">
                            <h3>PagerDuty</h3>
                            <p>Route critical incidents to on-call engineers</p>
                        </div>
                    </div>
                </>
            )
        },
        faq: {
            title: 'FAQ',
            content: (
                <>
                    <h2>Frequently Asked Questions</h2>

                    <div className="faq-item">
                        <h3>How does AI-powered incident analysis work?</h3>
                        <p>
                            We use advanced language models to analyze incident patterns and provide actionable insights.
                        </p>
                    </div>

                    <div className="faq-item">
                        <h3>What data do you collect?</h3>
                        <p>
                            Service health data, incident records, and usage analytics. See our <Link to="/privacy">Privacy Policy</Link>.
                        </p>
                    </div>
                </>
            )
        }
    }

    return (
        <div className="docs-page">
            <nav className="docs-nav">
                <Link to="/" className="nav-brand">
                    <span className="logo-icon">⬢</span>
                    <span className="logo-text">DevOps Sentinel</span>
                </Link>
                <Link to="/feedback" className="feedback-link">
                    Send Feedback
                </Link>
            </nav>

            <div className="docs-layout">
                <aside className="docs-sidebar">
                    <h3>Documentation</h3>
                    {Object.entries(sections).map(([key, section]) => (
                        <button
                            key={key}
                            className={`sidebar-item ${activeSection === key ? 'active' : ''}`}
                            onClick={() => setActiveSection(key)}
                        >
                            {section.title}
                        </button>
                    ))}
                </aside>

                <main className="docs-content">
                    {sections[activeSection].content}
                </main>
            </div>
        </div>
    )
}
