const AGENTS = [
  {
    code: '[A]',
    name: 'WATCHER',
    visual: '● ○ ○ ○',
    detail: 'Health, latency, SSL, and retries until a failure threshold is crossed.',
  },
  {
    code: '[B]',
    name: 'FIRST_RESPONDER',
    visual: '> ALERT',
    detail: 'Open an incident, keep evidence, and notify Slack or your on-call channel.',
  },
  {
    code: '[C]',
    name: 'INVESTIGATOR',
    visual: 'TIMELINE',
    detail: 'Checks, deployments, dependencies, and prior incidents stay attached.',
  },
  {
    code: '[D]',
    name: 'STRATEGIST',
    visual: 'PLAN + PM',
    detail: 'Response plan and postmortem. Destructive actions wait for human approval.',
  },
]

export default function AgentPipeline() {
  return (
    <div>
      <p className="section-kicker">THE_AGENT_LOOP</p>
      <div className="grid gap-6 sm:grid-cols-2">
        {AGENTS.map((agent) => (
          <article key={agent.name} className="diagram-box">
            <div className="diagram-label">
              {agent.code} {agent.name}
            </div>
            <div className="diagram-visual">{agent.visual}</div>
            <p className="text-[11px] leading-6 tracking-[0.05em] text-muted-foreground">{agent.detail}</p>
          </article>
        ))}
      </div>
    </div>
  )
}
