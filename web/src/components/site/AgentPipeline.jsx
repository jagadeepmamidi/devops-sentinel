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
    <ol className="relative m-0 grid gap-0 border-l border-border pl-6">
      {AGENTS.map((agent) => (
        <li key={agent.name} className="relative pb-8 last:pb-0">
          <span
            className="absolute top-1.5 -left-[1.6rem] size-2 rounded-sm bg-primary"
            aria-hidden="true"
          />
          <p className="text-xs text-muted-foreground">
            {agent.role}
          </p>
          <h3 className="mt-1 text-base font-semibold tracking-tight">{agent.name}</h3>
          <p className="mt-1 max-w-[42ch] text-sm leading-6 text-muted-foreground">{agent.detail}</p>
        </li>
      ))}
    </ol>
  )
}
