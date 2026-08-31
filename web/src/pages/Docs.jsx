import { useEffect, useMemo } from 'react'
import { Link, useLocation } from 'react-router-dom'
import CommandInstall from '../components/site/CommandInstall'
import LiveFailureDemo from '../components/site/LiveFailureDemo'
import SiteLayout from '../components/site/SiteLayout'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { GITHUB_URL, INSTALL_COMMAND, PYPI_URL } from '@/lib/site'

const SECTIONS = [
  { id: 'overview', title: 'Overview' },
  { id: 'quickstart', title: 'Quick start' },
  { id: 'demo', title: 'Demo' },
  { id: 'live-demo', title: 'Live 503' },
  { id: 'yaml', title: 'sentinel.yaml' },
  { id: 'local', title: 'Local mode' },
  { id: 'supabase', title: 'Your Supabase' },
  { id: 'commands', title: 'CLI reference' },
  { id: 'github', title: 'GitHub Action' },
  { id: 'agents', title: 'Response stages' },
  { id: 'mcp', title: 'MCP' },
  { id: 'operator', title: 'Operator console' },
  { id: 'faq', title: 'FAQ' },
]

function Code({ children, className = '' }) {
  return (
    <pre className={`overflow-x-auto border border-border bg-card p-4 font-mono text-[13px] leading-6 ${className}`.trim()}>
      {children}
    </pre>
  )
}

function Inline({ children }) {
  return (
    <code className="border border-border bg-card px-1.5 py-0.5 font-mono text-[12px]">
      {children}
    </code>
  )
}

export default function Docs() {
  const location = useLocation()
  const hashId = useMemo(
    () => (location.hash || '#overview').replace('#', ''),
    [location.hash],
  )
  const active = SECTIONS.some((section) => section.id === hashId) ? hashId : 'overview'

  useEffect(() => {
    const node = document.getElementById(active)
    if (node) {
      node.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, [active])

  return (
    <SiteLayout>
      <div className="page-wrap grid gap-8 py-10 lg:grid-cols-[200px_minmax(0,1fr)]">
        <aside className="lg:sticky lg:top-20 lg:self-start">
          <p className="mb-3 text-xs text-muted-foreground">Documentation</p>
          <nav className="flex gap-2 overflow-x-auto pb-2 lg:flex-col lg:overflow-visible" aria-label="Docs sections">
            {SECTIONS.map((section) => (
              <a
                key={section.id}
                href={`#${section.id}`}
                className={`whitespace-nowrap px-2 py-2 text-sm ${
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

        <article className="grid gap-12">
          <section id="overview" className="scroll-mt-24">
            <h1 className="max-w-[20ch] text-4xl font-semibold tracking-tight">
              CLI-first incident response, without giving us your data
            </h1>
            <p className="mt-4 max-w-2xl text-base leading-7 text-muted-foreground">
              Sentinel monitors HTTP endpoints, opens incidents after a failure threshold, and
              writes evidence to SQLite or to a Supabase project you control. The website is
              documentation and a live 503 demo for the CLI, not a hosted control plane.
            </p>
            <dl className="mt-6 divide-y divide-border border-y border-border">
              {[
                ['Install', 'PyPI package. No signup wall.'],
                ['Store', 'Local SQLite or bring-your-own Supabase.'],
                ['Respond', 'Incidents and labeled postmortems. No auto-remediation.'],
              ].map(([title, body]) => (
                <div key={title} className="grid gap-1 py-4 sm:grid-cols-[8rem_minmax(0,1fr)]">
                  <dt className="text-sm font-medium">{title}</dt>
                  <dd className="text-sm text-muted-foreground">{body}</dd>
                </div>
              ))}
            </dl>
          </section>

          <section id="quickstart" className="scroll-mt-24">
            <h2 className="text-2xl font-semibold tracking-tight">Quick start</h2>
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
sentinel demo
sentinel health https://api.example.com/health --expect 200 --json-path status --json-equals ok
sentinel services add production-api https://api.example.com/health
sentinel up --once`}</Code>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">3. Optional: your Supabase</CardTitle>
                </CardHeader>
                <CardContent className="grid gap-3">
                  <Code>{`sentinel init --mode supabase --url https://YOUR-PROJECT.supabase.co
sentinel login
sentinel supabase doctor`}</Code>
                  <p className="text-sm text-muted-foreground">
                    The CLI prompts for the anon key if you omit it. Apply{' '}
                    <Inline>supabase/schema.sql</Inline> in the SQL editor, or print it with{' '}
                    <Inline>sentinel schema</Inline>.
                  </p>
                </CardContent>
              </Card>
            </div>
          </section>

          <section id="demo" className="scroll-mt-24">
            <h2 className="text-2xl font-semibold tracking-tight">30-second demo</h2>
            <p className="mt-2 text-sm leading-7 text-muted-foreground">
              No API key, no third-party fail URL. Sentinel starts a local HTTP server with{' '}
              <Inline>/ok</Inline> (200) and <Inline>/fail</Inline> (503), registers the failing
              endpoint, opens an incident, and prints the next commands.
            </p>
            <Code>{`pip install devops-sentinel-next
sentinel demo`}</Code>
            <p className="mt-3 text-sm text-muted-foreground">
              After the card appears: <Inline>sentinel incidents list</Inline>, then{' '}
              <Inline>sentinel postmortem generate &lt;id&gt;</Inline>. Use{' '}
              <Inline>--keep-going</Inline> to keep polling until Ctrl+C.
            </p>
          </section>

          <section id="live-demo" className="scroll-mt-24">
            <h2 className="text-2xl font-semibold tracking-tight">Break this website from the CLI</h2>
            <p className="mt-2 text-sm leading-7 text-muted-foreground">
              Local <Inline>sentinel demo</Inline> spins up its own <Inline>/fail</Inline>. This
              page hosts a public probe so you can configure the CLI, press a button here, and
              watch HTTP 503 land in your terminal. The live URL stays 200 until you break it.{' '}
              <Inline>/api/demo/fail</Inline> is an always-on 503 if you just want a dummy error
              endpoint. On Windows PowerShell, run the two commands as separate lines —{' '}
              <Inline>&&</Inline> is not a statement separator there.
            </p>
            <div className="mt-4">
              <LiveFailureDemo />
            </div>
          </section>

          <section id="yaml" className="scroll-mt-24">
            <h2 className="text-2xl font-semibold tracking-tight">sentinel.yaml</h2>
            <p className="mt-2 text-sm leading-7 text-muted-foreground">
              Commit a project file next to the repo. <Inline>sentinel init</Inline> writes a sample
              if none exists. <Inline>sentinel up</Inline> registers missing services and starts
              the monitor.
            </p>
            <Code>{`services:
  - name: api
    url: https://api.example.com/health
    interval: 30
    failure_threshold: 3
    expect:
      status: [200]
      body: '"status": "ok"'
      json_path: status
      json_equals: ok
      ssl_min_days: 14`}</Code>
            <p className="mt-3 text-sm text-muted-foreground">
              Also accepted: <Inline>sentinel.yml</Inline>, <Inline>sentinel.json</Inline>. One-shot
              CI: <Inline>sentinel up --once</Inline>.
            </p>
          </section>

          <section id="local" className="scroll-mt-24">
            <h2 className="text-2xl font-semibold tracking-tight">Local mode</h2>
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
            <h2 className="text-2xl font-semibold tracking-tight">Bring your own Supabase</h2>
            <p className="mt-2 text-sm leading-7 text-muted-foreground">
              Sentinel does not operate a shared database for customers. If you want team auth and
              Postgres, you create the project, you keep the keys, you own the rows.
            </p>
            <ol className="mt-4 grid gap-3 text-sm leading-6 text-muted-foreground">
              <li>1. Create a project at supabase.com. This is yours, not ours.</li>
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
              <li>
                5. <Inline>sentinel supabase doctor</Inline> checks URL, anon key, REST, tables, and
                RLS without writing data.
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
            <h2 className="text-2xl font-semibold tracking-tight">CLI reference</h2>
            <div className="mt-4 overflow-x-auto border border-border">
              <table className="w-full min-w-[520px] text-left text-[12px]">
                <thead className="border-b border-border font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
                  <tr>
                    <th className="px-4 py-3">Command</th>
                    <th className="px-4 py-3">What it does</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    ['sentinel init [--mode local|supabase]', 'Create .env, sentinel.yaml, and local identity or BYO Supabase config'],
                    ['sentinel demo', 'Local 503 loop: open an incident and print the next commands'],
                    ['GET /api/demo/live/:id  (this site)', 'Healthy until you press Break on the website; then HTTP 503 for two minutes'],
                    ['sentinel up [--once]', 'Register services from sentinel.yaml and monitor them'],
                    ['sentinel login [--local|--device|--token]', 'Local identity, or auth against your Supabase'],
                    ['sentinel schema [--print]', 'Show or print the SQL your project needs'],
                    ['sentinel health <url>', 'One check. Always reports TLS days on HTTPS. --ssl-min-days fails when remaining days are low. Exit 1 when unhealthy'],
                    ['sentinel monitor <name|url> [--all] [--once] [--notify]', 'Continuous checks. A raw URL is auto-registered. --notify posts SLACK_WEBHOOK_URL'],
                    ['sentinel services add|list|check', 'Register and probe endpoints'],
                    ['sentinel watch', 'Alias for monitor'],
                    ['sentinel dashboard [--once]', 'Live terminal table of registered services'],
                    ['sentinel incidents list|show|ack|resolve|export', 'Incident memory and timeline'],
                    ['sentinel postmortem generate|view', 'OpenRouter/OpenAI write-up when a key is set; otherwise a local template'],
                    ['sentinel agents', 'Print the Watcher → Strategist workflow'],
                    ['sentinel doctor', 'Mode-aware diagnostics'],
                    ['sentinel supabase doctor', 'Probe YOUR Supabase URL, key, tables, and RLS'],
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

          <section id="github" className="scroll-mt-24">
            <h2 className="text-2xl font-semibold tracking-tight">GitHub Action</h2>
            <p className="mt-2 text-sm leading-7 text-muted-foreground">
              Official composite action for a one-shot health probe. Copy{' '}
              <Inline>examples/github-health.yml</Inline> into your repo. Do not add a flaky
              public-URL check as a required status on this project.
            </p>
            <Code>{`jobs:
  health:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: jagadeepmamidi/devops-sentinel/.github/actions/sentinel-health@main
        with:
          url: https://api.example.com/health
          expect: "200"
          json-path: status
          json-equals: ok
          ssl-min-days: "14"`}</Code>
          </section>

          <section id="agents" className="scroll-mt-24">
            <h2 className="text-2xl font-semibold tracking-tight">Incident-response stages</h2>
            <p className="mt-2 text-sm leading-7 text-muted-foreground">
              This is the CLI pipeline. It is not a CrewAI or multi-agent runtime. Remediation
              with side effects is not executed automatically.
            </p>
            <Code>{`Health check
  → Detect     failure, latency, SSL
  → Open       persist incident, optional Slack
  → Plan       template postmortem (or LLM if a key is set)
  → Human      destructive remediation is not auto-executed`}</Code>
            <p className="mt-3 text-sm text-muted-foreground">
              Optional AI keys: <Inline>sentinel config set openrouter_api_key</Inline>. Default
              model is <Inline>openai/gpt-4o-mini</Inline>. Without a key, or if the model call
              fails, postmortems still generate from collected evidence.
            </p>
          </section>

          <section id="mcp" className="scroll-mt-24">
            <h2 className="text-2xl font-semibold tracking-tight">MCP</h2>
            <p className="mt-2 text-sm leading-7 text-muted-foreground">
              Expose read-only operational context to Cursor, Claude Desktop, and other MCP hosts.
            </p>
            <Code>{`pip install "devops-sentinel-next[mcp]"   # mcp 1.x FastMCP
sentinel mcp`}</Code>
            <p className="mt-3 text-sm text-muted-foreground">
              The extra pins mcp 1.x so FastMCP tool registration works.
              Paste this into Cursor <Inline>.cursor/mcp.json</Inline> (or Claude Desktop MCP
              settings). Full example: <Inline>examples/mcp.json</Inline>.
            </p>
            <Code>{`{
  "mcpServers": {
    "devops-sentinel": {
      "command": "sentinel",
      "args": ["mcp"]
    }
  }
}`}</Code>
            <p className="mt-3 text-sm text-muted-foreground">
              Tools: health_check, doctor, list_incidents, get_incident, get_incident_events,
              analyze_anomaly, generate_postmortem. Do not expose remote MCP to the public internet
              without auth, rate limits, and audit logs.
            </p>
          </section>

          <section id="operator" className="scroll-mt-24">
            <h2 className="text-2xl font-semibold tracking-tight">Optional operator console</h2>
            <p className="mt-2 text-sm leading-7 text-muted-foreground">
              The pages under <Inline>/operator</Inline> talk to a FastAPI process you run. They
              are not a hosted SaaS dashboard. In local mode they read the same SQLite store as the
              CLI — no bearer token. <Inline>sentinel serve</Inline> binds localhost by default.
              Do not pass <Inline>--host 0.0.0.0</Inline> unless you intend to expose that API.
            </p>
            <Code>{`sentinel serve
# local mode: open /operator/services — no token
# supabase mode: paste a bearer token from your session`}</Code>
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
            <h2 className="text-2xl font-semibold tracking-tight">FAQ</h2>
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
                    <Inline>{INSTALL_COMMAND}</Inline>. Package:{' '}
                    <a className="text-foreground underline" href={PYPI_URL} target="_blank" rel="noopener noreferrer">
                      PyPI
                    </a>
                    . Source:{' '}
                    <a className="text-foreground underline" href={GITHUB_URL} target="_blank" rel="noopener noreferrer">
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
