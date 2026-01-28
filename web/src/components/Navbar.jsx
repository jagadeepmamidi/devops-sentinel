import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import './Navbar.css'

export default function Navbar() {
    const { user, signOut } = useAuth()
    const navigate = useNavigate()
    const location = useLocation()

    const handleSignOut = async () => {
        await signOut()
        navigate('/')
    }

    const navLinks = [
        { path: '/dashboard', label: 'Overview' },
        { path: '/projects', label: 'Projects' },
        { path: '/incidents', label: 'Incidents' },
        { path: '/postmortems', label: 'Postmortems' }
    ]

    return (
        <nav className="navbar">
            <div className="nav-brand" onClick={() => navigate('/dashboard')}>
                <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
                    <rect width="32" height="32" rx="8" fill="url(#gradient)" />
                    <path d="M16 8L22 12V20L16 24L10 20V12L16 8Z" stroke="white" strokeWidth="2" fill="none" />
                    <circle cx="16" cy="16" r="3" fill="white" />
                    <defs>
                        <linearGradient id="gradient" x1="0" y1="0" x2="32" y2="32">
                            <stop offset="0%" stopColor="#ffffff" />
                            <stop offset="100%" stopColor="#888888" />
                        </linearGradient>
                    </defs>
                </svg>
                <span>DevOps Sentinel</span>
            </div>

            <div className="nav-links">
                {navLinks.map(link => (
                    <button
                        key={link.path}
                        className={`nav-link ${location.pathname === link.path ? 'active' : ''}`}
                        onClick={() => navigate(link.path)}
                    >
                        {link.label}
                    </button>
                ))}
            </div>

            <div className="nav-user">
                <div className="user-avatar">
                    {user?.email?.[0]?.toUpperCase() || 'U'}
                </div>
                <div className="user-menu">
                    <span className="user-email">{user?.email}</span>
                    <button className="btn btn-ghost btn-sm" onClick={handleSignOut}>
                        Sign Out
                    </button>
                </div>
            </div>
        </nav>
    )
}
