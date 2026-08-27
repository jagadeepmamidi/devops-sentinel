const AGENTS = [
  {
    name: 'Watcher',
    role: 'Detect',
    detail: 'Health, latency, SSL, and retries until a failure threshold is crossed.',
  },
  {
    name: 'First Responder',
    role: 'Alert',
    detail: 'Open an incident, keep evidence, and notify Slack or your on-call channel.',
  },
  {
    name: 'Investigator',
    role: 'Correlate',
    detail: 'Timeline, deployments, dependencies, and prior incidents stay attached.',
  },
  {
    name: 'Strategist',
    role: 'Plan',
    detail: 'Response plan and postmortem. Destructive actions wait for human approval.',
  },
]

export default function AgentPipeline() {
  return (
    <div className="grid gap-10 lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)] lg:items-end lg:gap-16">
      <div className="max-w-[65ch]">
        <h2 className="text-3xl font-medium tracking-tight text-balance sm:text-4xl">
          Four roles. One approval boundary.
        </h2>
        <p className="mt-4 max-w-[42ch] text-sm leading-7 text-muted-foreground">
          Sentinel coordinates agents in the terminal. They recommend. They do not change
          infrastructure unless you approve it.
        </p>
      </div>
      <ol className="relative">
        <span
          className="absolute bottom-4 left-[7px] top-4 w-px bg-gradient-to-b from-white/25 via-white/10 to-transparent"
          aria-hidden="true"
        />
        {AGENTS.map((agent, index) => (
          <li
            key={agent.name}
            className="relative grid grid-cols-[16px_minmax(0,1fr)] gap-4 py-4"
            style={{ paddingRight: `${Math.max(0, 3 - index) * 5}%` }}
          >
            <span className="relative z-10 mt-1.5 size-2 rounded-full border border-white/40 bg-zinc-950 shadow-[0_0_0_4px_rgba(12,12,14,0.95)]" />
            <div>
              <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                <h3 className="text-base font-medium">{agent.name}</h3>
                <span className="text-sm text-muted-foreground">{agent.role}</span>
              </div>
              <p className="mt-1 max-w-[65ch] text-sm leading-6 text-muted-foreground">
                {agent.detail}
              </p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  )
}
