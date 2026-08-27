const AGENTS = [
  {
    id: '01',
    name: 'Watcher',
    role: 'Detect',
    detail: 'Health, latency, SSL, and retries until a failure threshold is crossed.',
  },
  {
    id: '02',
    name: 'First Responder',
    role: 'Alert',
    detail: 'Open an incident, keep evidence, and notify Slack or your on-call channel.',
  },
  {
    id: '03',
    name: 'Investigator',
    role: 'Correlate',
    detail: 'Timeline, deployments, dependencies, and prior incidents stay attached.',
  },
  {
    id: '04',
    name: 'Strategist',
    role: 'Plan',
    detail: 'Response plan and postmortem. Destructive actions wait for human approval.',
  },
]

export default function AgentPipeline() {
  return (
    <div className="grid gap-8 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)] lg:gap-16">
      <div className="max-w-[65ch]">
        <h2 className="text-3xl font-medium tracking-tight text-balance">
          Four roles. One approval boundary.
        </h2>
        <p className="mt-4 text-sm leading-7 text-muted-foreground">
          Sentinel coordinates agents in the terminal. They recommend. They do not change
          infrastructure unless you approve it.
        </p>
      </div>
      <ol className="grid gap-0">
        {AGENTS.map((agent, index) => (
          <li
            key={agent.id}
            className={`grid grid-cols-[auto_minmax(0,1fr)] gap-4 py-5 ${
              index === 0 ? '' : 'border-t border-white/10'
            }`}
          >
            <span className="font-mono text-xs text-muted-foreground">{agent.id}</span>
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
