const DEFAULT_LINES = [
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
  warn: 'text-live',
  sys: 'text-foreground',
}

export default function TerminalReplay({
  title = 'SENTINEL / LOCAL',
  meta = 'SQLITE',
  lines = DEFAULT_LINES,
  tall = false,
}) {
  return (
    <div className={`terminal-frame ${tall ? 'h-[280px]' : ''}`}>
      <div className="terminal-frame-header font-mono text-[10px] tracking-[0.12em]">
        <span>{title}</span>
        <span>{meta}</span>
      </div>
      <pre
        className="m-0 overflow-x-auto pt-8 font-mono text-[11px] leading-6 tracking-normal normal-case"
        aria-label="Sample Sentinel terminal session"
      >
        {lines.map((line, index) => (
          <span
            key={`${line.text}-${index}`}
            className={`terminal-line block ${TONE_CLASS[line.tone] || TONE_CLASS.dim}`}
            style={{ animationDelay: `${0.08 + index * 0.12}s` }}
          >
            {line.time ? (
              <>
                <span className="mr-3 text-[#555]">{line.time}</span>
                {line.tag ? (
                  <span className={`mr-3 inline-block w-10 ${TONE_CLASS[line.tone]}`}>{line.tag}</span>
                ) : null}
              </>
            ) : null}
            {line.text}
          </span>
        ))}
      </pre>
    </div>
  )
}
