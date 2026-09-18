import { cn } from '@/lib/utils'

function StatusLamp({ tone = 'idle', label }) {
  return (
    <span className="terminal-status">
      <span className={`terminal-status-lamp terminal-status-lamp--${tone}`} aria-hidden="true" />
      {label}
    </span>
  )
}

export default function TerminalWindow({
  title,
  meta,
  status,
  actions,
  children,
  className,
  bodyClassName,
}) {
  return (
    <figure className={cn('terminal-window', className)}>
      <figcaption className="terminal-window-bar">
        <span className="terminal-window-title">{title}</span>
        <span className="terminal-window-meta">
          {status ? <StatusLamp tone={status.tone} label={status.label} /> : meta}
          {actions}
        </span>
      </figcaption>
      <div className={cn('terminal-window-body', bodyClassName)}>{children}</div>
    </figure>
  )
}
