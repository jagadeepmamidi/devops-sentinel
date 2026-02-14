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
          <div className="docs-feature-grid">
            <div className="docs-feature-card">
              <h4>Intelligent Monitoring</h4>
              <p>ML-powered anomaly detection catches issues before they become incidents.</p>
            </div>
            <div className="docs-feature-card">
              <h4>AI Analysis</h4>
              <p>Automatic postmortems and root cause analysis powered by advanced AI.</p>
            </div>
            <div className="docs-feature-card">
              <h4>Smart Alerting</h4>
              <p>Context-aware alerts with severity-based routing and escalation.</p>
            </div>
            <div className="docs-feature-card">
              <h4>Dependency Mapping</h4>
              <p>Visualize service dependencies and predict cascade failures.</p>
            </div>
            <div className="docs-feature-card">
              <h4>Deployment Tracking</h4>
              <p>Correlate incidents with deployments and suggest rollbacks.</p>
            </div>
            <div className="docs-feature-card">
              <h4>Team Collaboration</h4>
              <p>Slack integration, on-call schedules, and incident timelines.</p>
            </div>
          </div>
        </>
      ),
    },
    quickstart: {
      title: 'Quick Start',
      content: (
        <>
          <h2>Get Started in 5 Minutes</h2>
          <p>
            Preferred flow: install CLI, run <code>sentinel login</code>, complete signup/signin
            in browser, then return to terminal and start monitoring.
          </p>

          <div className="docs-step-card">
            <div className="docs-step-number">1</div>
            <div className="docs-step-content">
              <h3>Install the CLI</h3>
              <p>Install DevOps Sentinel from PyPI.</p>
              <div className="docs-code-block">
                <code>pip install devops-sentinel</code>
              </div>
            </div>
          </div>

          <div className="docs-step-card">
            <div className="docs-step-number">2</div>
            <div className="docs-step-content">
              <h3>Login via Browser Flow</h3>
              <p>Run login in terminal, complete sign-in in browser, then return to CLI.</p>
              <div className="docs-code-block">
                <code>
                  sentinel login<br />
                  # browser opens /cli-auth<br />
                  # returns to local callback
                </code>
              </div>
            </div>
          </div>

          <div className="docs-step-card">
            <div className="docs-step-number">3</div>
            <div className="docs-step-content">
              <h3>Add and Monitor a Service</h3>
              <p>Register your health URL and begin continuous checks.</p>
              <div className="docs-code-block">
                <code>
                  sentinel services add my-api https://api.example.com/health<br />
                  sentinel monitor https://api.example.com/health
                </code>
              </div>
            </div>
          </div>

          <div className="docs-step-card">
            <div className="docs-step-number">4</div>
            <div className="docs-step-content">
              <h3>Validate and Operate</h3>
              <p>
                Use <code>sentinel doctor</code> to verify environment health and
                <code> sentinel incidents list</code> to track incidents.
              </p>
            </div>
          </div>
        </>
      ),
    },
    features: {
      title: 'Features',
      content: (
        <>
          <h2>Core Features</h2>

          <div className="docs-feature-detail">
            <h3>Failure Classification</h3>
            <p>
              Intelligent incident detection with confidence scoring to prevent alert fatigue.
              Automatically classifies failures by severity (P0-P3).
            </p>
          </div>

          <div className="docs-feature-detail">
            <h3>Incident Memory</h3>
            <p>
              AI-powered similarity search finds similar past incidents and suggests proven
              remediation steps.
            </p>
          </div>

          <div className="docs-feature-detail">
            <h3>Dependency Analysis</h3>
            <p>
              Build service dependency graphs to calculate blast radius and predict cascade
              failures.
            </p>
          </div>

          <div className="docs-feature-detail">
            <h3>ML Anomaly Detection</h3>
            <p>
              Machine learning detects anomalies in response times, error rates, and traffic
              patterns.
            </p>
          </div>

          <div className="docs-feature-detail">
            <h3>On-Call Management</h3>
            <p>
              Schedule rotations with weekly/daily shifts, overrides, and multi-level escalation.
            </p>
          </div>

          <div className="docs-feature-detail">
            <h3>Deployment Correlation</h3>
            <p>
              Track deployments and correlate with incidents to suggest rollbacks.
            </p>
          </div>
        </>
      ),
    },
    api: {
      title: 'API Reference',
      content: (
        <>
          <h2>API Documentation</h2>
          <p>Access DevOps Sentinel programmatically via REST API.</p>

          <h3>Authentication</h3>
          <div className="docs-code-block">
            <code>
              curl -H "Authorization: Bearer YOUR_API_KEY" \<br />
              &nbsp;&nbsp;https://api.devops-sentinel.dev/v1/services
            </code>
          </div>

          <h3>Endpoints</h3>

          <div className="docs-api-endpoint">
            <div className="docs-api-method get">GET</div>
            <div className="docs-api-path">/v1/services</div>
            <p>List all monitored services.</p>
          </div>

          <div className="docs-api-endpoint">
            <div className="docs-api-method post">POST</div>
            <div className="docs-api-path">/v1/incidents</div>
            <p>Create incident.</p>
          </div>
        </>
      ),
    },
    integrations: {
      title: 'Integrations',
      content: (
        <>
          <h2>Connect Your Tools</h2>

          <div className="docs-integration-card">
            <div className="docs-integration-content">
              <h3>Slack</h3>
              <p>Get incident alerts in Slack with threaded updates.</p>
            </div>
          </div>

          <div className="docs-integration-card">
            <div className="docs-integration-content">
              <h3>PagerDuty</h3>
              <p>Route critical incidents to on-call engineers.</p>
            </div>
          </div>
        </>
      ),
    },
    faq: {
      title: 'FAQ',
      content: (
        <>
          <h2>Frequently Asked Questions</h2>

          <div className="docs-faq-item">
            <h3>How does AI-powered incident analysis work?</h3>
            <p>
              We use advanced language models to analyze incident patterns and provide actionable
              insights.
            </p>
          </div>

          <div className="docs-faq-item">
            <h3>What data do you collect?</h3>
            <p>
              Service health data, incident records, and usage analytics. See our{' '}
              <Link to="/privacy">Privacy Policy</Link>.
            </p>
          </div>
        </>
      ),
    },
  }

  return (
    <div className="docs-page">
      <a className="docs-skip-link" href="#docs-main">Skip to content</a>
      <div className="docs-grid-overlay" aria-hidden="true" />

      <nav className="docs-nav">
        <Link to="/" className="docs-brand">
          <span className="docs-logo-icon">S</span>
          <span className="docs-logo-text">DevOps Sentinel</span>
        </Link>
        <div className="docs-nav-links">
          <Link to="/cli-auth">CLI Auth</Link>
          <Link to="/feedback" className="docs-feedback-link">
            Send Feedback
          </Link>
        </div>
      </nav>

      <div className="docs-shell">
        <header className="docs-hero">
          <p className="docs-hero-label">Reference</p>
          <h1>Operator documentation for CLI-first incident response</h1>
          <p>
            Use this guide to install, authenticate, monitor services, and integrate incident
            workflows with your existing stack.
          </p>
          <div className="docs-hero-command">
            <span>$</span>
            <code>sentinel login && sentinel monitor &lt;health-url&gt;</code>
          </div>
        </header>

        <div className="docs-layout">
          <aside className="docs-sidebar">
            <h3>Documentation</h3>
            {Object.entries(sections).map(([key, section]) => (
              <button
                key={key}
                type="button"
                className={`docs-sidebar-item ${activeSection === key ? 'active' : ''}`}
                onClick={() => setActiveSection(key)}
              >
                {section.title}
              </button>
            ))}
          </aside>

          <main id="docs-main" className="docs-content">
            {sections[activeSection].content}
          </main>
        </div>
      </div>
    </div>
  )
}

