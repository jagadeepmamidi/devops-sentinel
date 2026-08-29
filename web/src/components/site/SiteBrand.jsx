import { Link } from 'react-router-dom'

export default function SiteBrand({ to = '/', onNavigate }) {
  return (
    <Link
      to={to}
      className="inline-flex items-center gap-2 text-foreground no-underline"
      aria-label="DevOps Sentinel home"
      onClick={onNavigate}
    >
      <span className="text-primary" aria-hidden="true">
        &gt;_
      </span>
      <span className="text-sm font-semibold tracking-tight">sentinel</span>
    </Link>
  )
}
