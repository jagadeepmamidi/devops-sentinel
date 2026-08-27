import { Link } from 'react-router-dom'

export default function SiteBrand({ to = '/', onNavigate }) {
  return (
    <Link
      to={to}
      className="inline-flex items-center gap-2.5 text-foreground no-underline"
      aria-label="DevOps Sentinel home"
      onClick={onNavigate}
    >
      <span
        className="grid size-7 place-items-center rounded-md bg-primary font-mono text-xs font-semibold text-primary-foreground"
        aria-hidden="true"
      >
        S
      </span>
      <span className="text-sm font-semibold tracking-tight">DevOps Sentinel</span>
    </Link>
  )
}
