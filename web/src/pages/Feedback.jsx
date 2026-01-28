import { useState } from 'react'
import { Link } from 'react-router-dom'
import './Feedback.css'

export default function Feedback() {
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        type: 'feedback',
        message: ''
    })
    const [submitted, setSubmitted] = useState(false)

    const handleSubmit = async (e) => {
        e.preventDefault()

        // TODO: Send to backend
        console.log('Feedback submitted:', formData)

        setSubmitted(true)
        setTimeout(() => {
            setSubmitted(false)
            setFormData({ name: '', email: '', type: 'feedback', message: '' })
        }, 3000)
    }

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        })
    }

    return (
        <div className="feedback-page">
            <nav className="feedback-nav">
                <Link to="/" className="nav-brand">
                    <span className="logo-icon">⬢</span>
                    <span className="logo-text">DevOps Sentinel</span>
                </Link>
            </nav>

            <div className="feedback-container">
                <div className="feedback-header">
                    <h1>Send Feedback</h1>
                    <p>Help us improve DevOps Sentinel. We read every message.</p>
                </div>

                {submitted ? (
                    <div className="success-message">
                        <h2>Thank You!</h2>
                        <p>Your feedback has been received. We'll review it shortly.</p>
                    </div>
                ) : (
                    <form className="feedback-form" onSubmit={handleSubmit}>
                        <div className="form-row">
                            <div className="form-group">
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

                            <div className="form-group">
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

                        <div className="form-group">
                            <label htmlFor="type">Type</label>
                            <select
                                id="type"
                                name="type"
                                value={formData.type}
                                onChange={handleChange}
                            >
                                <option value="feedback">General Feedback</option>
                                <option value="bug">Bug Report</option>
                                <option value="feature">Feature Request</option>
                                <option value="question">Question</option>
                            </select>
                        </div>

                        <div className="form-group">
                            <label htmlFor="message">Message</label>
                            <textarea
                                id="message"
                                name="message"
                                rows="8"
                                value={formData.message}
                                onChange={handleChange}
                                placeholder="Tell us what's on your mind..."
                                required
                            />
                        </div>

                        <button type="submit" className="submit-btn">
                            Submit Feedback
                        </button>
                    </form>
                )}

                <div className="feedback-footer">
                    <p>You can also reach us at <a href="mailto:feedback@devops-sentinel.dev">feedback@devops-sentinel.dev</a></p>
                </div>
            </div>
        </div>
    )
}
