import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

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
    <Card className="border-border bg-card">
      <CardHeader className="gap-2">
        <Badge variant="outline" className="w-fit font-mono text-[10px] uppercase tracking-widest">
          Multi-agent loop
        </Badge>
        <CardTitle className="text-xl tracking-tight">
          Four roles. One approval boundary.
        </CardTitle>
        <p className="text-sm leading-6 text-muted-foreground">
          Sentinel coordinates agents in the terminal. They recommend; they do not change
          infrastructure unless you approve it.
        </p>
      </CardHeader>
      <CardContent className="grid gap-3 sm:grid-cols-2">
        {AGENTS.map((agent) => (
          <article
            key={agent.id}
            className="rounded-lg border border-border bg-secondary/20 p-4"
          >
            <div className="mb-2 flex items-center justify-between gap-3">
              <span className="font-mono text-[11px] text-muted-foreground">{agent.id}</span>
              <Badge variant="secondary">{agent.role}</Badge>
            </div>
            <h3 className="text-sm font-medium">{agent.name}</h3>
            <p className="mt-1 text-sm leading-6 text-muted-foreground">{agent.detail}</p>
          </article>
        ))}
      </CardContent>
    </Card>
  )
}
