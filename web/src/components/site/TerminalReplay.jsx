const LINES = [
  { tone: 'dim', text: '$ sentinel init' },
  { tone: 'ok', text: 'OK  Local mode ready. No Supabase or login required.' },
  { tone: 'dim', text: '$ sentinel services add production-api https://api.example.com/health' },
  { tone: 'ok', text: 'OK  Registered production-api' },
  { tone: 'dim', text: '$ sentinel monitor production-api --failure-threshold 3' },
  { tone: 'ok', text: 'production-api HEALTHY | HTTP 200 | 84ms | check #1' },
  { tone: 'warn', text: 'production-api DEGRADED | HTTP 503 | 1120ms | check #4' },
  { tone: 'dim', text: 'Watcher opened incident · First Responder notified · Strategist drafting plan' },
]

const TONE_CLASS = {
  dim: 'text-muted-foreground',
  ok: 'text-primary',
  warn: 'text-amber-300',
}

export default function TerminalReplay() {
  return (
    <div className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
      <div className="grid grid-cols-[1fr_auto_1fr] items-center border-b border-border px-4 py-3 font-mono text-[11px] text-muted-foreground">
        <span className="flex gap-1.5" aria-hidden="true">
          <i className="size-1.5 rounded-full bg-muted-foreground/50" />
          <i className="size-1.5 rounded-full bg-muted-foreground/50" />
          <i className="size-1.5 rounded-full bg-muted-foreground/50" />
        </span>
        <span>sentinel / local</span>
        <span className="justify-self-end">SQLite</span>
      </div>
      <pre
        className="m-0 overflow-x-auto p-5 font-mono text-[13px] leading-7"
        aria-label="Sample Sentinel terminal session"
      >
        {LINES.map((line) => (
          <span key={line.text} className={`block ${TONE_CLASS[line.tone]}`}>
            {line.text}
          </span>
        ))}
      </pre>
    </div>
  )
}
