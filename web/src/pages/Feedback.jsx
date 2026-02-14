import { useState } from 'react'
import SiteTopNav from '../components/site/SiteTopNav'
import SiteFooter from '../components/site/SiteFooter'
import './Feedback.css'

const NAV_LINKS = [
  { to: '/docs', label: 'Docs' },
  { to: '/', label: 'Home' },
]

const FOOTER_LINKS = [
  { to: '/terms', label: 'Terms' },
  { to: '/privacy', label: 'Privacy' },
  { to: '/about', label: 'About' },
]

export default function Feedback() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    type: 'feedback',
    message: '',
  })
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = async (event) => {
    event.preventDefault()

    // TODO: send to backend endpoint
    console.log('Feedback submitted:', formData)

    setSubmitted(true)
    setTimeout(() => {
      setSubmitted(false)
      setFormData({ name: '', email: '', type: 'feedback', message: '' })
    }, 3000)
  }

  const handleChange = (event) => {
    setFormData((previous) => ({
      ...previous,
      [event.target.name]: event.target.value,
    }))
  }

  return (
    <div className="site-page feedback-page">
      <a className="site-skip-link" href="#feedback-main">Skip to content</a>

      <SiteTopNav links={NAV_LINKS} />

      <main id="feedback-main" className="site-main site-container feedback-main">
        <section className="site-card feedback-header-card">
          <p className="site-label">Feedback</p>
          <h1 className="site-title">Help us improve DevOps Sentinel</h1>
          <p className="site-text">We review every report and use it to prioritize roadmap work.</p>
        </section>

        {submitted ? (
          <section className="site-card soft feedback-success">
            <h2>Thanks for your feedback</h2>
            <p className="site-text">Your message was received successfully.</p>
          </section>
        ) : (
          <section className="site-card feedback-form-card">
            <form className="feedback-form" onSubmit={handleSubmit}>
              <div className="feedback-row">
                <div className="feedback-field">
                  <label htmlFor="name">Name</label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div className="feedback-field">
                  <label htmlFor="email">Email</label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                  />
                </div>
              </div>

              <div className="feedback-field">
                <label htmlFor="type">Type</label>
                <select id="type" name="type" value={formData.type} onChange={handleChange}>
                  <option value="feedback">General Feedback</option>
                  <option value="bug">Bug Report</option>
                  <option value="feature">Feature Request</option>
                  <option value="question">Question</option>
                </select>
              </div>

              <div className="feedback-field">
                <label htmlFor="message">Message</label>
                <textarea
                  id="message"
                  name="message"
                  rows="8"
                  value={formData.message}
                  onChange={handleChange}
                  placeholder="Describe feedback, issue, or request"
                  required
                />
              </div>

              <button type="submit" className="site-btn primary feedback-submit-btn">
                Submit feedback
              </button>
            </form>
          </section>
        )}
      </main>

      <SiteFooter links={FOOTER_LINKS} text="DevOps Sentinel feedback" />
    </div>
  )
}
