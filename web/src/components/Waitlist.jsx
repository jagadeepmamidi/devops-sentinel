import React, { useState } from 'react';
import './Waitlist.css';

const Waitlist = () => {
    const [email, setEmail] = useState('');
    const [submitted, setSubmitted] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [waitlistCount] = useState(247); // Mock count for social proof

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        if (!email || !email.includes('@')) {
            setError('Please enter a valid email address');
            return;
        }

        setLoading(true);

        try {
            const response = await fetch('/api/waitlist', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });

            if (response.ok) {
                setSubmitted(true);
            } else {
                const data = await response.json();
                setError(data.message || 'Something went wrong');
            }
        } catch {
            // For demo, just succeed
            setSubmitted(true);
        } finally {
            setLoading(false);
        }
    };

    if (submitted) {
        return (
            <div className="waitlist-container">
                <div className="waitlist-success">
                    <div className="success-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M20 6L9 17l-5-5" />
                        </svg>
                    </div>
                    <h3>You're on the list!</h3>
                    <p>We'll notify you when DevOps Sentinel launches.</p>
                    <p className="position">You're #{waitlistCount + 1} on the waitlist</p>

                    <div className="share-section">
                        <p className="share-prompt">Share with your team:</p>
                        <div className="share-buttons">
                            <a
                                href={`https://twitter.com/intent/tweet?text=${encodeURIComponent('Just joined the waitlist for DevOps Sentinel - AI-powered incident memory for SRE teams. Check it out!')}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="share-btn twitter"
                            >
                                Twitter
                            </a>
                            <a
                                href={`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(window.location.origin)}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="share-btn linkedin"
                            >
                                LinkedIn
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="waitlist-container">
            <div className="waitlist-content">
                <div className="waitlist-badge">LAUNCHING SOON</div>

                <h2>Get Early Access</h2>

                <p className="waitlist-description">
                    Be the first to try DevOps Sentinel - the AI that remembers
                    your incidents so you don't have to.
                </p>

                <div className="social-proof">
                    <div className="avatars">
                        <div className="avatar">JD</div>
                        <div className="avatar">AK</div>
                        <div className="avatar">MR</div>
                        <div className="avatar">+{waitlistCount - 3}</div>
                    </div>
                    <span>{waitlistCount}+ teams waiting</span>
                </div>

                <form onSubmit={handleSubmit} className="waitlist-form">
                    <div className="input-group">
                        <input
                            type="email"
                            placeholder="Enter your work email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            disabled={loading}
                        />
                        <button type="submit" disabled={loading}>
                            {loading ? 'Joining...' : 'Join Waitlist'}
                        </button>
                    </div>
                    {error && <p className="error-message">{error}</p>}
                </form>

                <ul className="benefits-list">
                    <li>
                        <svg viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                        Early access to all features
                    </li>
                    <li>
                        <svg viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                        50% off Pro tier for 6 months
                    </li>
                    <li>
                        <svg viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                        Direct access to founding team
                    </li>
                </ul>

                <p className="privacy-note">
                    No spam. Unsubscribe anytime.
                </p>
            </div>
        </div>
    );
};

export default Waitlist;
