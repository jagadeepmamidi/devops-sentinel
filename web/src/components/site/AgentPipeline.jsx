const STAGES = [
  {
    name: 'Detect',
    role: 'Health check',
    detail: 'HTTP status, latency, SSL, and retries until a failure threshold is crossed.',
  },
  {
    name: 'Open',
    role: 'Incident',
    detail: 'Persist the incident, keep evidence, and optionally notify Slack.',
  },
  {
    name: 'Plan',
    role: 'Postmortem',
    detail: 'Template report by default. Optional LLM draft when you set a key — fallback is labeled.',
  },
  {
    name: 'Human',
    role: 'Approval',
    detail: 'Destructive remediation is not executed automatically.',
  },
]

export default function AgentPipeline() {
  return (
    <ol className="relative m-0 grid gap-0 border-l border-border pl-6">
      {STAGES.map((stage) => (
        <li key={stage.name} className="relative pb-8 last:pb-0">
          <span
            className="absolute top-1.5 -left-[1.6rem] size-2 rounded-sm bg-primary"
            aria-hidden="true"
          />
          <p className="text-xs text-muted-foreground">{stage.role}</p>
          <h3 className="mt-1 text-base font-semibold tracking-tight">{stage.name}</h3>
          <p className="mt-1 max-w-[42ch] text-sm leading-6 text-muted-foreground">{stage.detail}</p>
        </li>
      ))}
    </ol>
  )
}
