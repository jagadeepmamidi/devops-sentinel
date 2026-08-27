import { Link } from 'react-router-dom'

export default function SiteBrand({ to = '/', onNavigate }) {
  return (
    <Link
      to={to}
      className="inline-flex items-center gap-2 pr-1 text-foreground no-underline"
      aria-label="DevOps Sentinel home"
      onClick={onNavigate}
    >
      <span
        className="grid size-6 place-items-center rounded-full bg-gradient-to-br from-zinc-100 via-zinc-300 to-zinc-600 font-mono text-[10px] font-semibold text-zinc-950 shadow-[inset_0_1px_0_rgba(255,255,255,0.7),0_0_0_1px_rgba(255,255,255,0.18)]"
        aria-hidden="true"
      >
        S
      </span>
      <span className="text-[13px] font-medium tracking-tight">DevOps Sentinel</span>
    </Link>
  )
}
