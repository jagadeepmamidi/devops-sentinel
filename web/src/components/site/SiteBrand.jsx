import { Link } from 'react-router-dom'

export default function SiteBrand({ to = '/', onNavigate }) {
  return (
    <Link
      to={to}
      className="inline-flex items-center gap-3 text-foreground no-underline hover:bg-transparent"
      aria-label="DevOps Sentinel home"
      onClick={onNavigate}
    >
      <span
        className="grid size-8 place-items-center border-2 border-live font-mono text-sm font-bold text-primary"
        aria-hidden="true"
      >
        &gt;_
      </span>
      <span className="text-[1.35rem] font-extrabold tracking-[-0.02em]">
        SENTINEL
        <i className="cursor-block" aria-hidden="true" />
      </span>
    </Link>
  )
}
