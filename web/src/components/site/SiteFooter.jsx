import { Link } from 'react-router-dom'

export default function SiteFooter({ links = [], text = 'DevOps Sentinel' }) {
  return (
    <footer className="site-footer site-container">
      <span className="site-footer-text">{text}</span>
      <div className="site-footer-links">
        {links.map((item) => (
          <Link key={item.key || item.label} to={item.to} className="site-footer-link">
            {item.label}
          </Link>
        ))}
      </div>
    </footer>
  )
}
