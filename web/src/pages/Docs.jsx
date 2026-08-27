import { useEffect, useMemo } from 'react'
import { Link, useLocation } from 'react-router-dom'
import CommandInstall from '../components/site/CommandInstall'
import SiteLayout from '../components/site/SiteLayout'
import { Button } from '@/components/ui/button'
import { GITHUB_URL, INSTALL_COMMAND } from '@/lib/site'

const SECTIONS = [
  { id: 'overview', title: 'Overview' },
  { id: 'quickstart', title: 'Quick start' },
  { id: 'demo', title: 'Demo' },
  { id: 'yaml', title: 'sentinel.yaml' },
  { id: 'local', title: 'Local mode' },
  { id: 'supabase', title: 'Your Supabase' },
  { id: 'commands', title: 'CLI reference' },
  { id: 'github', title: 'GitHub Action' },
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
      <div className="mx-auto grid w-full max-w-6xl gap-8 px-4 py-10 sm:px-6 lg:grid-cols-[220px_minmax(0,1fr)]">
        <aside className="lg:sticky lg:top-20 lg:self-start">
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
            <h1 className="text-4xl font-medium tracking-tight text-balance">
              CLI-first incident response, without giving us your data
            </h1>
            <p className="mt-4 max-w-2xl text-base leading-7 text-muted-foreground">
              Sentinel monitors HTTP endpoints, opens incidents after a failure threshold, runs a
              staged agent workflow, and writes evidence to SQLite or to a Supabase project you
              control. The website is documentation and a browser helper for your own auth - not a
              hosted control plane.
            </p>
            <dl className="mt-8 grid gap-6 sm:grid-cols-2">
              <div className="border-l border-white/12 pl-4">
                <dt className="text-sm font-medium">Install</dt>
                <dd className="mt-1 text-sm text-muted-foreground">PyPI package. No signup wall.</dd>
              </div>
              <div className="border-l border-white/12 pl-4">
                <dt className="text-sm font-medium">Store</dt>
                <dd className="mt-1 text-sm text-muted-foreground">
                  Local SQLite or bring-your-own Supabase. Agents propose. Humans approve.
                </dd>
              </div>
            </dl>
          </section>

          <section id="quickstart" className="scroll-mt-24">
            <h2 className="text-2xl font-medium tracking-tight">Quick start</h2>
            <p className="mt-2 text-sm leading-7 text-muted-foreground">
              Local mode is the default. Login is only required if you connect your own Supabase.
            </p>
            <div className="mt-6 grid gap-8">
              <div className="border-l border-white/12 pl-5">
                <h3 className="text-base font-medium">Install</h3>
                <div className="mt-3">
                  <CommandInstall note="Package name is devops-sentinel-next." />
                </div>
              </div>
              <div className="border-l border-white/12 pl-5">
                <h3 className="text-base font-medium">Initialize locally</h3>
                <Code className="mt-3">{`sentinel init
sentinel demo
sentinel health https://api.example.com/health --expect 200 --json-path status --json-equals ok
sentinel services add production-api https://api.example.com/health
sentinel up --once`}</Code>
              </div>
              <div className="border-l border-white/12 pl-5">
                <h3 className="text-base font-medium">Optional: your Supabase</h3>
                <Code className="mt-3">{`sentinel init --mode supabase --url https://YOUR-PROJECT.supabase.co
sentinel login
sentinel supabase doctor`}</Code>
                <p className="mt-3 text-sm text-muted-foreground">
                  The CLI prompts for the anon key if you omit it. Apply{' '}
                  <Inline>supabase/schema.sql</Inline> in the SQL editor, or print it with{' '}
                  <Inline>sentinel schema</Inline>.
                </p>
              </div>
            </div>
          </section>

          <section id="demo" className="scroll-mt-24">
            <h2 className="text-2xl font-medium tracking-tight">30-second demo</h2>
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

          <section id="yaml" className="scroll-mt-24">
            <h2 className="text-2xl font-medium tracking-tight">sentinel.yaml</h2>
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
              <li>1. Create a project at supabase.com - this is yours, not ours.</li>
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
                    ['sentinel init [--mode local|supabase]', 'Create .env, sentinel.yaml, and local identity or BYO Supabase config'],
                    ['sentinel demo', 'Local 503 loop: open an incident and print the next commands'],
                    ['sentinel up [--once]', 'Register services from sentinel.yaml and monitor them'],
                    ['sentinel login [--local|--device|--token]', 'Local identity, or auth against your Supabase'],
                    ['sentinel schema [--print]', 'Show or print the SQL your project needs'],
                    ['sentinel health <url>', 'One check. --expect, --body, --json-path, --ssl-min-days. Exit 1 when unhealthy'],
                    ['sentinel services add|list|check', 'Register and probe endpoints'],
                    ['sentinel monitor <name|url> [--all] [--once]', 'Continuous checks with failure/recovery thresholds'],
                    ['sentinel watch', 'Alias for monitor'],
                    ['sentinel dashboard', 'Live terminal table of registered services'],
                    ['sentinel incidents list|show|ack|resolve|export', 'Incident memory and timeline'],
                    ['sentinel postmortem generate|view', 'Fallback or AI-assisted write-up'],
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
            <h2 className="text-2xl font-medium tracking-tight">GitHub Action</h2>
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
sentinel mcp`}</Code>
            <p className="mt-3 text-sm text-muted-foreground">
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
            <dl className="mt-6 divide-y divide-white/8 border-y border-white/8">
              <div className="py-4">
                <dt className="text-sm font-medium">Do I have to log in?</dt>
                <dd className="mt-2 text-sm text-muted-foreground">
                  No. Local mode works offline. Login is for your Supabase project, CI tokens, or
                  device flow.
                </dd>
              </div>
              <div className="py-4">
                <dt className="text-sm font-medium">Where does data go?</dt>
                <dd className="mt-2 text-sm text-muted-foreground">
                  SQLite on disk, or tables in your Supabase. See the{' '}
                  <Link className="text-foreground underline" to="/privacy">
                    privacy policy
                  </Link>
                  .
                </dd>
              </div>
              <div className="py-4">
                <dt className="text-sm font-medium">What is the install package name?</dt>
                <dd className="mt-2 text-sm text-muted-foreground">
                  <Inline>{INSTALL_COMMAND}</Inline>. Source:{' '}
                  <a className="text-foreground underline" href={GITHUB_URL}>
                    GitHub
                  </a>
                  .
                </dd>
              </div>
            </dl>
          </section>
        </article>
      </div>
    </SiteLayout>
  )
}
