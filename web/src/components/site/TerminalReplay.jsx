import TerminalWindow from './TerminalWindow'

const DEFAULT_LINES = [
  { tone: 'dim', text: '$ sentinel init' },
  { tone: 'ok', text: 'OK  Local mode ready. No Supabase or login required.' },
  { tone: 'dim', text: '$ sentinel services add production-api https://api.example.com/health' },
  { tone: 'ok', text: 'OK  Registered production-api' },
  { tone: 'dim', text: '$ sentinel monitor production-api --failure-threshold 3' },
  { tone: 'ok', text: 'production-api HEALTHY | HTTP 200 | 84ms | check #1' },
  { tone: 'warn', text: 'production-api DEGRADED | HTTP 503 | 1120ms | check #4' },
  { tone: 'dim', text: 'INCIDENT OPENED after 3 consecutive failures. Next: sentinel incidents show <id>' },
]

const TONE_CLASS = {
  dim: 'text-muted-foreground',
  ok: 'text-primary',
  warn: 'text-destructive',
  sys: 'text-foreground',
}

export default function TerminalReplay({
  title = 'sentinel / local',
  meta = 'sqlite',
  lines = DEFAULT_LINES,
}) {
  return (
    <TerminalWindow title={title} meta={meta}>
      <pre className="terminal-session" aria-label="Sample Sentinel terminal session">
        {lines.map((line, index) => (
          <span
            key={`${line.text}-${index}`}
            className={`terminal-line block ${TONE_CLASS[line.tone] || TONE_CLASS.dim}`}
            style={{ animationDelay: `${0.08 + index * 0.1}s` }}
          >
            {line.text}
          </span>
        ))}
        <span className="terminal-line mt-1 block text-primary" style={{ animationDelay: `${0.08 + lines.length * 0.1}s` }}>
          ${' '}
          <span className="terminal-caret" aria-hidden="true" />
        </span>
      </pre>
    </TerminalWindow>
  )
}
