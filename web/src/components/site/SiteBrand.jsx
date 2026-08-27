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
        className="grid size-7 place-items-center rounded-md bg-gradient-to-br from-zinc-100 via-zinc-300 to-zinc-600 font-mono text-xs font-semibold text-zinc-950 shadow-[inset_0_1px_0_rgba(255,255,255,0.7),0_0_0_1px_rgba(255,255,255,0.18)]"
        aria-hidden="true"
      >
        S
      </span>
      <span className="text-sm font-semibold tracking-tight">DevOps Sentinel</span>
    </Link>
  )
}
