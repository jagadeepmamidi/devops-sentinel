import { Link } from 'react-router-dom'

export default function SiteBrand({ to = '/' }) {
  return (
    <Link to={to} className="site-brand" aria-label="DevOps Sentinel home">
      <span className="site-brand-badge">S</span>
      <span className="site-brand-text">DevOps Sentinel</span>
    </Link>
  )
}
