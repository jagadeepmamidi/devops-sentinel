import SiteTopNav from '../components/site/SiteTopNav'
import SiteFooter from '../components/site/SiteFooter'
import './Legal.css'

const NAV_LINKS = [
  { to: '/privacy', label: 'Privacy' },
  { to: '/docs', label: 'Docs' },
]

const FOOTER_LINKS = [
  { to: '/about', label: 'About' },
  { to: '/privacy', label: 'Privacy' },
  { to: '/docs', label: 'Docs' },
]

export default function Terms() {
  return (
    <div className="site-page legal-page">
      <a className="site-skip-link" href="#legal-main">Skip to content</a>

      <SiteTopNav links={NAV_LINKS} />

      <main id="legal-main" className="site-main site-container legal-main">
        <article className="site-card legal-content-card">
          <p className="site-label">Terms of Service</p>
          <h1 className="site-title">Terms of Service</h1>
          <p className="legal-last-updated">Last updated: January 28, 2026</p>

          <section>
            <h2>Acceptance of terms</h2>
            <p>
              By using DevOps Sentinel, you agree to these terms. If you do not agree, do not use
              the service.
            </p>
          </section>

          <section>
            <h2>Service description</h2>
            <p>
              DevOps Sentinel provides service monitoring, incident workflows, and related
              operational tooling through CLI and web interfaces.
            </p>
          </section>

          <section>
            <h2>Account responsibilities</h2>
            <ul>
              <li>Keep credentials secure</li>
              <li>Maintain accurate account information</li>
              <li>Report unauthorized access promptly</li>
            </ul>
          </section>

          <section>
            <h2>Acceptable use</h2>
            <ul>
              <li>Do not use the service for illegal activity</li>
              <li>Do not attempt unauthorized access or abuse platform limits</li>
              <li>Only monitor services you are authorized to monitor</li>
            </ul>
          </section>

          <section>
            <h2>Limitation of liability</h2>
            <p>
              The service is provided "as is" without warranties. Liability is limited to the
              amount paid by you for the service in the preceding 12 months.
            </p>
          </section>

          <section>
            <h2>Termination</h2>
            <p>
              We may suspend or terminate access for violation of these terms. You may request
              account termination at any time.
            </p>
          </section>

          <section>
            <h2>Contact</h2>
            <p>
              Questions about terms: <a href="mailto:legal@devops-sentinel.dev">legal@devops-sentinel.dev</a>
            </p>
          </section>
        </article>
      </main>

      <SiteFooter links={FOOTER_LINKS} text="DevOps Sentinel legal" />
    </div>
  )
}
