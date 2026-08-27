import { useEffect, useMemo, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import CommandInstall from '../components/site/CommandInstall'
import SiteLayout from '../components/site/SiteLayout'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { GITHUB_URL, INSTALL_COMMAND } from '@/lib/site'

const SECTIONS = [
  { id: 'overview', title: 'Overview' },
  { id: 'quickstart', title: 'Quick start' },
  { id: 'local', title: 'Local mode' },
  { id: 'supabase', title: 'Your Supabase' },
  { id: 'commands', title: 'CLI reference' },
  { id: 'agents', title: 'Agents' },
  { id: 'mcp', title: 'MCP' },
  { id: 'operator', title: 'Operator console' },
  { id: 'faq', title: 'FAQ' },
]

function Code({ children, className = '' }) {
  return (
    <pre className={`overflow-x-auto rounded-lg border border-border bg-secondary/40 p-4 font-mono text-[13px] leading-6 ${className}`.trim()}>
      {children}
    </pre>
  )
}

function Inline({ children }) {
  return (
    <code className="rounded-md border border-border bg-secondary/50 px-1.5 py-0.5 font-mono text-[12px]">
      {children}
    </code>
  )
}

export default function Docs() {
  const location = useLocation()
  const [active, setActive] = useState('overview')

  const hashId = useMemo(
    () => (location.hash || '#overview').replace('#', ''),
    [location.hash],
  )

  useEffect(() => {
    const next = SECTIONS.some((section) => section.id === hashId) ? hashId : 'overview'
    setActive(next)
    const node = document.getElementById(next)
    if (node) {
      node.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, [hashId])

  return (
    <SiteLayout>
      <div className="mx-auto grid w-full max-w-6xl gap-8 px-4 py-10 sm:px-6 lg:grid-cols-[220px_minmax(0,1fr)]">
        <aside className="lg:sticky lg:top-24 lg:self-start">
          <p className="mb-3 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            Documentation
          </p>
          <nav className="flex gap-2 overflow-x-auto pb-2 lg:flex-col lg:overflow-visible" aria-label="Docs sections">
            {SECTIONS.map((section) => (
              <a
                key={section.id}
                href={`#${section.id}`}
                className={`whitespace-nowrap rounded-md px-3 py-2 text-sm ${
                  active === section.id
                    ? 'bg-secondary text-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
                aria-current={active === section.id ? 'location' : undefined}
              >
                {section.title}
              </a>
            ))}
          </nav>
        </aside>

        <article className="grid gap-10">
          <section id="overview" className="scroll-mt-24">
            <Badge variant="outline">Operator guide</Badge>
            <h1 className="mt-4 text-4xl font-medium tracking-tight">
              CLI-first incident response, without giving us your data
            </h1>
            <p className="mt-4 max-w-2xl text-base leading-7 text-muted-foreground">
              Sentinel monitors HTTP endpoints, opens incidents after a failure threshold, runs a
              staged agent workflow, and writes evidence to SQLite or to a Supabase project you
              control. The website is documentation and a browser helper for your own auth — not a
              hosted control plane.
            </p>
            <div className="mt-6 grid gap-3 sm:grid-cols-3">
              {[
                ['Install', 'PyPI package. No signup wall.'],
                ['Store', 'Local SQLite or bring-your-own Supabase.'],
                ['Respond', 'Agents propose. Humans approve.'],
              ].map(([title, body]) => (
                <Card key={title}>
                  <CardHeader>
                    <CardTitle className="text-base">{title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">{body}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>

          <section id="quickstart" className="scroll-mt-24">
            <h2 className="text-2xl font-medium tracking-tight">Quick start</h2>
            <p className="mt-2 text-sm leading-7 text-muted-foreground">
              Local mode is the default. Login is only required if you connect your own Supabase.
            </p>
            <div className="mt-4 grid gap-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">1. Install</CardTitle>
                </CardHeader>
                <CardContent>
                  <CommandInstall note="Package name is devops-sentinel-next." />
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">2. Initialize locally</CardTitle>
                </CardHeader>
                <CardContent>
                  <Code>{`sentinel init
sentinel health https://api.example.com/health
sentinel services add production-api https://api.example.com/health
sentinel monitor production-api --failure-threshold 3`}</Code>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">3. Optional: your Supabase</CardTitle>
                </CardHeader>
                <CardContent className="grid gap-3">
                  <Code>{`sentinel init --mode supabase --url https://YOUR-PROJECT.supabase.co
sentinel login
sentinel doctor`}</Code>
                  <p className="text-sm text-muted-foreground">
                    The CLI prompts for the anon key if you omit it. Apply{' '}
                    <Inline>supabase/schema.sql</Inline> in the SQL editor, or print it with{' '}
                    <Inline>sentinel schema</Inline>.
                  </p>
                </CardContent>
              </Card>
            </div>
          </section>

          <section id="local" className="scroll-mt-24">
            <h2 className="text-2xl font-medium tracking-tight">Local mode</h2>
            <p className="mt-2 text-sm leading-7 text-muted-foreground">
              No account, no API server, no Sentinel-hosted database. Identity is{' '}
              <Inline>local@localhost</Inline>. Data lives in <Inline>.sentinel/sentinel.db</Inline>.
            </p>
            <Code>{`SENTINEL_MODE=local
SENTINEL_DATA_DIR=.sentinel
OPENROUTER_API_KEY=
SLACK_WEBHOOK_URL=`}</Code>
            <p className="mt-3 text-sm text-muted-foreground">
              Useful commands: <Inline>sentinel whoami</Inline>, <Inline>sentinel config</Inline>,{' '}
              <Inline>sentinel doctor</Inline>, <Inline>sentinel dashboard</Inline>.
            </p>
          </section>

          <section id="supabase" className="scroll-mt-24">
            <h2 className="text-2xl font-medium tracking-tight">Bring your own Supabase</h2>
            <p className="mt-2 text-sm leading-7 text-muted-foreground">
              Sentinel does not operate a shared database for customers. If you want team auth and
              Postgres, you create the project, you keep the keys, you own the rows.
            </p>
            <ol className="mt-4 grid gap-3 text-sm leading-6 text-muted-foreground">
              <li>1. Create a project at supabase.com — this is yours, not ours.</li>
              <li>
                2. Run the schema: <Inline>sentinel schema --print</Inline> or copy{' '}
                <Inline>supabase/schema.sql</Inline> into the SQL editor.
              </li>
              <li>
                3. Enable Email / Google / GitHub in your Auth providers if you want browser login.
              </li>
              <li>
                4. <Inline>sentinel init --mode supabase</Inline> then <Inline>sentinel login</Inline>.
                Browser login talks to <strong className="text-foreground">your</strong> project.
              </li>
            </ol>
            <Code className="mt-4">{`SENTINEL_MODE=supabase
SUPABASE_URL=https://YOUR-PROJECT.supabase.co
SUPABASE_ANON_KEY=your-anon-key`}</Code>
            <p className="mt-3 text-sm text-muted-foreground">
              Headless or SSH: <Inline>sentinel login --device</Inline> or{' '}
              <Inline>sentinel login --token</Inline> for CI.
            </p>
          </section>

          <section id="commands" className="scroll-mt-24">
            <h2 className="text-2xl font-medium tracking-tight">CLI reference</h2>
            <div className="mt-4 overflow-x-auto rounded-xl border border-border">
              <table className="w-full min-w-[520px] text-left text-sm">
                <thead className="border-b border-border bg-secondary/40 font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
                  <tr>
                    <th className="px-4 py-3">Command</th>
                    <th className="px-4 py-3">What it does</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    ['sentinel init [--mode local|supabase]', 'Create .env and local identity or BYO Supabase config'],
                    ['sentinel login [--local|--device|--token]', 'Local identity, or auth against your Supabase'],
                    ['sentinel schema [--print]', 'Show or print the SQL your project needs'],
                    ['sentinel health <url>', 'One check. Exit 1 when unhealthy'],
                    ['sentinel services add|list|check', 'Register and probe endpoints'],
                    ['sentinel monitor <name|url> [--all]', 'Continuous checks with failure/recovery thresholds'],
                    ['sentinel watch', 'Alias for monitor'],
                    ['sentinel dashboard', 'Live terminal table of registered services'],
                    ['sentinel incidents list|show|ack|resolve|export', 'Incident memory and timeline'],
                    ['sentinel postmortem generate|view', 'Fallback or AI-assisted write-up'],
                    ['sentinel agents', 'Print the Watcher → Strategist workflow'],
                    ['sentinel doctor', 'Mode-aware diagnostics'],
                    ['sentinel config set|list|remove', 'Store provider keys in ~/.sentinel/config.json'],
                    ['sentinel mcp / devops-sentinel-mcp', 'Read-only tools for Cursor and Claude Desktop'],
                    ['sentinel serve', 'Optional local FastAPI for the operator console'],
                    ['sentinel completion bash|zsh|fish|powershell', 'Shell completions'],
                  ].map(([command, detail]) => (
                    <tr key={command} className="border-b border-border last:border-0">
                      <td className="px-4 py-3 font-mono text-xs">{command}</td>
                      <td className="px-4 py-3 text-muted-foreground">{detail}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section id="agents" className="scroll-mt-24">
            <h2 className="text-2xl font-medium tracking-tight">Multi-agent workflow</h2>
            <p className="mt-2 text-sm leading-7 text-muted-foreground">
              Each role has a narrow job and evidence context. Remediation with side effects is
              blocked until a human approves it.
            </p>
            <Code>{`Health check
  → Watcher           detect failure, latency, SSL, anomaly
  → First Responder   open incident, notify
  → Investigator      correlate checks, events, deployments
  → Strategist        action plan + postmortem
  → Human approval    required before destructive remediation`}</Code>
            <p className="mt-3 text-sm text-muted-foreground">
              Optional AI keys: <Inline>sentinel config set openrouter_api_key</Inline>. Without a
              key, postmortems still generate from collected evidence.
            </p>
          </section>

          <section id="mcp" className="scroll-mt-24">
            <h2 className="text-2xl font-medium tracking-tight">MCP</h2>
            <p className="mt-2 text-sm leading-7 text-muted-foreground">
              Expose read-only operational context to Cursor, Claude Desktop, and other MCP hosts.
            </p>
            <Code>{`pip install "devops-sentinel-next[mcp]"
devops-sentinel-mcp`}</Code>
            <p className="mt-3 text-sm text-muted-foreground">
              Tools: health_check, doctor, list_incidents, get_incident, get_incident_events,
              analyze_anomaly, generate_postmortem. Do not expose remote MCP to the public internet
              without auth, rate limits, and audit logs.
            </p>
          </section>

          <section id="operator" className="scroll-mt-24">
            <h2 className="text-2xl font-medium tracking-tight">Optional operator console</h2>
            <p className="mt-2 text-sm leading-7 text-muted-foreground">
              The pages under <Inline>/operator</Inline> talk to a FastAPI process you run. They
              are not a hosted SaaS dashboard. Start the API, then paste a bearer token from your
              session.
            </p>
            <Code>{`sentinel serve
# then open /operator/services and paste a token`}</Code>
            <div className="mt-4 flex flex-wrap gap-3">
              <Button asChild variant="outline">
                <Link to="/operator/services">Open operator services</Link>
              </Button>
              <Button asChild variant="outline">
                <Link to="/cli-auth">CLI auth helper</Link>
              </Button>
            </div>
          </section>

          <section id="faq" className="scroll-mt-24">
            <h2 className="text-2xl font-medium tracking-tight">FAQ</h2>
            <div className="mt-4 grid gap-3">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Do I have to log in?</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">
                    No. Local mode works offline. Login is for your Supabase project, CI tokens, or
                    device flow.
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Where does data go?</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">
                    SQLite on disk, or tables in your Supabase. See the{' '}
                    <Link className="text-foreground underline" to="/privacy">
                      privacy policy
                    </Link>
                    .
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">What is the install package name?</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">
                    <Inline>{INSTALL_COMMAND}</Inline>. Source:{' '}
                    <a className="text-foreground underline" href={GITHUB_URL}>
                      GitHub
                    </a>
                    .
                  </p>
                </CardContent>
              </Card>
            </div>
          </section>
        </article>
      </div>
    </SiteLayout>
  )
}
