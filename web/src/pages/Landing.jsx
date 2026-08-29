import { Link } from 'react-router-dom'
import AgentPipeline from '../components/site/AgentPipeline'
import CommandInstall from '../components/site/CommandInstall'
import SiteLayout from '../components/site/SiteLayout'
import TerminalReplay from '../components/site/TerminalReplay'
import { GITHUB_URL } from '@/lib/site'

const HEALTH_LOG = [
  { time: '00:00.00', tag: 'SYS', tone: 'sys', text: 'WATCHER_START production-api' },
  { time: '00:00.08', tag: 'EXEC', tone: 'sys', text: 'CHECK https://api.example.com/health' },
  { time: '00:00.17', tag: 'OK', tone: 'ok', text: 'HTTP 200 84ms' },
  { time: '00:00.18', tag: 'SYS', tone: 'sys', text: 'SQLITE_WRITE check #1' },
  { time: '00:00.24', tag: 'EXEC', tone: 'sys', text: 'CHECK checkout-worker /ready' },
  { time: '00:00.31', tag: 'OK', tone: 'ok', text: 'HTTP 200 112ms' },
  { time: '00:00.90', tag: 'WARN', tone: 'warn', text: 'HTTP 503 1120ms' },
  { time: '00:00.91', tag: 'SYS', tone: 'sys', text: 'INCIDENT_OPENED' },
  { time: '00:01.02', tag: 'SYS', tone: 'sys', text: 'FIRST_RESPONDER notified' },
  { time: '00:01.10', tag: 'SYS', tone: 'sys', text: 'STRATEGIST drafting plan' },
]

const MODELS = [
  {
    code: '[A]',
    name: 'CLI_FIRST',
    visual: '$ sentinel',
    body: 'Install, init, monitor, and generate postmortems without a hosted account.',
  },
  {
    code: '[B]',
    name: 'YOUR_STORE',
    visual: '.sentinel/db',
    body: 'Local SQLite, or connect the Supabase project you already own. Sentinel never keeps a copy.',
  },
  {
    code: '[C]',
    name: 'SAFE_AGENTS',
    visual: 'HUMAN_OK',
    body: 'Agents propose the next move. Anything with side effects waits for a human.',
  },
  {
    code: '[D]',
    name: 'HEALTH_SURFACE',
    visual: 'HTTP 200',
    body: 'Latency, status, SSL, retries, and JSON-path checks. Continuous, not a dashboard you babysit.',
  },
  {
    code: '[E]',
    name: 'MCP_READY',
    visual: 'stdio',
    body: 'Read-only operational context for Cursor, Claude, and other MCP hosts.',
  },
  {
    code: '[F]',
    name: 'SELF_HOST',
    visual: 'sentinel serve',
    body: 'Optional operator UI talks to an API you run. There is no Sentinel-hosted control plane.',
  },
]

const HEALTH_ROWS = [
  { name: 'api-gateway', url: '/health', latency: '84 ms', status: 'HEALTHY' },
  { name: 'checkout-worker', url: '/ready', latency: '112 ms', status: 'HEALTHY' },
  { name: 'edge-cache', url: '/ping', latency: '96 ms', status: 'WATCHING' },
]

export default function Landing() {
  return (
    <SiteLayout hud>
      <div className="site-grid pb-8">
        <section className="col-span-full border-b-0 pt-16 pb-10 md:pt-28 md:pb-16">
          <div className="mb-8 flex items-center gap-3">
            <span
              className="grid size-12 place-items-center border-2 border-live text-lg font-bold text-primary"
              aria-hidden="true"
            >
              &gt;_
            </span>
            <span className="text-[clamp(1.8rem,4vw,2.6rem)] font-extrabold tracking-[-0.02em]">
              SENTINEL
              <i className="cursor-block" aria-hidden="true" />
            </span>
          </div>
          <h1 className="max-w-[900px] text-[clamp(2rem,5vw,4.5rem)] font-extrabold leading-none tracking-[-0.02em]">
            Watch the endpoint. Keep the incident in your own store.
          </h1>
          <p className="subtitle mt-4 max-w-[40ch] text-[1.15rem] font-normal tracking-[-0.01em] text-foreground normal-case">
            Local-first health checks, incident memory, and agent response.
          </p>

          <div className="mt-16 grid grid-cols-1 gap-8 lg:grid-cols-12">
            <div className="lg:col-span-6">
              <p className="max-w-[45ch] text-[12px] leading-6 tracking-[0.05em] text-muted-foreground">
                DevOps Sentinel is a local-first CLI for health checks, multi-agent incident
                response, and postmortems. SQLite by default. Optional login against{' '}
                <strong className="font-bold text-foreground">your</strong> Supabase project. We do
                not host or store your operational data.
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <Link to="/docs#quickstart" className="btn-raw">
                  GET_STARTED
                </Link>
                <Link to="/docs#agents" className="btn-raw">
                  AGENT_LOOP
                </Link>
              </div>
              <div className="mt-6">
                <CommandInstall />
              </div>
            </div>
            <div className="lg:col-span-6">
              <TerminalReplay
                title="JOB: HEALTH_MESH"
                meta="TIME_ELAPSED: 1.10s"
                lines={HEALTH_LOG}
              />
            </div>
          </div>
        </section>

        <section className="col-span-full border-b border-border py-16 md:py-24">
          <h2 className="section-kicker">01 THE_SIGNAL</h2>
          <div className="grid gap-8 lg:grid-cols-12">
            <p className="max-w-[35ch] text-[14px] leading-6 text-foreground lg:col-span-6">
              Hosted SRE platforms ask you to ship telemetry into their cloud. Sentinel does the opposite.
            </p>
            <div className="lg:col-span-6">
              <p className="max-w-[45ch] text-[12px] leading-6 tracking-[0.05em] text-muted-foreground">
                Most on-call tools were built as SaaS: minutes to log in, a dashboard you babysit,
                and incident memory that lives on someone else&apos;s disk.
              </p>
              <p className="mt-4 max-w-[45ch] text-[12px] leading-6 tracking-[0.05em] text-muted-foreground">
                Sentinel checks endpoints you already own, writes evidence next to the repo or into
                a database you provision, and stops agents at human approval.
              </p>
            </div>
          </div>
        </section>

        <section className="col-span-full border-b border-border py-16 md:py-24">
          <h2 className="section-kicker">02 EXECUTION_MODEL</h2>
          <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
            {MODELS.map((item) => (
              <article key={item.name} className="diagram-box">
                <div className="diagram-label">
                  {item.code} {item.name}
                </div>
                <div className="diagram-visual normal-case tracking-normal">{item.visual}</div>
                <p className="text-[11px] leading-6 tracking-[0.05em] text-muted-foreground">{item.body}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="col-span-full border-b border-border py-16 md:py-24">
          <h2 className="section-kicker">03 ARCHITECTURE_DELTA</h2>
          <div className="grid gap-10 lg:grid-cols-12">
            <ul className="data-list lg:col-span-6">
              <li>
                <strong>LOCAL-FIRST PARITY</strong>
                <span className="text-muted-foreground">
                  `sentinel init` writes SQLite under `.sentinel/`. No account, no API server, no
                  Sentinel-hosted database.
                </span>
              </li>
              <li>
                <strong>BRING YOUR SUPABASE</strong>
                <span className="text-muted-foreground">
                  Team mode is `sentinel init --mode supabase` against your project URL and anon key.
                  Auth, incidents, and postmortems stay in that project.
                </span>
              </li>
            </ul>
            <ul className="data-list lg:col-span-6">
              <li>
                <strong>AGENT-OPERABLE</strong>
                <span className="text-muted-foreground">
                  Four roles coordinate in the terminal. They recommend. They do not change
                  infrastructure unless you approve it.
                </span>
              </li>
              <li>
                <strong>DENY-BY-DEFAULT</strong>
                <span className="text-muted-foreground">
                  Destructive remediation is an explicit approval, not a default. Keys stay in your
                  config store.
                </span>
              </li>
            </ul>
          </div>
        </section>

        <section className="col-span-full border-b border-border py-16 md:py-24">
          <h2 className="section-kicker">04 THE_AGENT_LOOP</h2>
          <div className="grid items-start gap-10 lg:grid-cols-12">
            <div className="lg:col-span-6">
              <AgentPipeline />
            </div>
            <div className="lg:col-span-6">
              <TerminalReplay
                title="SENTINEL CLI"
                meta="LOOP: DETECT → PLAN"
                lines={[
                  { tone: 'dim', text: '$ sentinel monitor production-api' },
                  { tone: 'ok', text: '→ CHECK #1 HEALTHY  HTTP 200  84ms' },
                  { tone: 'warn', text: '→ CHECK #4 DEGRADED HTTP 503  1120ms' },
                  { tone: 'sys', text: '→ INCIDENT OPENED  evidence attached' },
                  { tone: 'sys', text: '$ sentinel incidents show inc_4f2' },
                  { tone: 'ok', text: '→ STRATEGIST drafted response plan' },
                  { tone: 'dim', text: '$ sentinel postmortem generate inc_4f2' },
                  { tone: 'ok', text: '→ WROTE postmortem.md  [human approval still required]' },
                ]}
                tall
              />
            </div>
          </div>
        </section>

        <section className="col-span-full border-b border-border py-16 md:py-24">
          <h2 className="section-kicker">05 HEALTH_SURFACE</h2>
          <div className="grid gap-10 lg:grid-cols-12">
            <div className="lg:col-span-7">
              <table className="spec-table">
                <tbody>
                  {HEALTH_ROWS.map((row) => (
                    <tr key={row.name}>
                      <td className="spec-key">
                        <span className="block text-foreground normal-case tracking-normal">{row.name}</span>
                        <span className="normal-case tracking-normal">{row.url}</span>
                      </td>
                      <td className="spec-value">
                        <span className={row.status === 'WATCHING' ? 'text-live' : 'text-primary'}>
                          {row.status}
                        </span>
                        <span className="ml-4 text-muted-foreground">{row.latency}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <Link to="/docs#commands" className="btn-raw mt-6">
                CLI_REFERENCE
              </Link>
            </div>
            <div className="lg:col-span-5">
              <p className="max-w-[40ch] text-[14px] leading-6 text-foreground">
                Continuous checks, not a dashboard you babysit.
              </p>
              <p className="mt-4 max-w-[45ch] text-[12px] leading-6 tracking-[0.05em] text-muted-foreground">
                HTTP 2xx and 3xx count as reachable. Failure and recovery thresholds keep a single
                blip from opening or closing an incident.
              </p>
            </div>
          </div>
        </section>

        <section className="col-span-full border-b border-border py-16 md:py-24">
          <h2 className="section-kicker">06 SYSTEM_SPECS</h2>
          <div className="grid gap-10 lg:grid-cols-12">
            <table className="spec-table lg:col-span-6">
              <tbody>
                <tr>
                  <td className="spec-key">RUNTIME</td>
                  <td className="spec-value">Python 3.10+. PyPI package devops-sentinel-next.</td>
                </tr>
                <tr>
                  <td className="spec-key">DEFAULT_STORE</td>
                  <td className="spec-value">SQLite at .sentinel/sentinel.db. Identity local@localhost.</td>
                </tr>
                <tr>
                  <td className="spec-key">TEAM_MODE</td>
                  <td className="spec-value">Bring-your-own Supabase. You keep the keys and the rows.</td>
                </tr>
                <tr>
                  <td className="spec-key">CHECKS</td>
                  <td className="spec-value">Status, body, JSON path, SSL days, retries, thresholds.</td>
                </tr>
              </tbody>
            </table>
            <table className="spec-table lg:col-span-6">
              <tbody>
                <tr>
                  <td className="spec-key">AGENTS</td>
                  <td className="spec-value">Watcher, First Responder, Investigator, Strategist.</td>
                </tr>
                <tr>
                  <td className="spec-key">SAFETY</td>
                  <td className="spec-value">Recommend only. Destructive work needs explicit approval.</td>
                </tr>
                <tr>
                  <td className="spec-key">MCP</td>
                  <td className="spec-value">Optional stdio tools for Cursor and Claude Desktop.</td>
                </tr>
                <tr>
                  <td className="spec-key">OPERATOR_UI</td>
                  <td className="spec-value">Optional. sentinel serve, then paste a bearer token.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section className="col-span-full py-16 md:py-24">
          <h2 className="section-kicker">07 INSTALL_CLI</h2>
          <div className="grid items-start gap-8 lg:grid-cols-12">
            <div className="lg:col-span-7">
              <p className="max-w-[40ch] text-[14px] leading-6 text-foreground">
                Install once. Monitor from the terminal you already use.
              </p>
              <div className="mt-6">
                <CommandInstall />
              </div>
            </div>
            <div className="flex flex-wrap gap-3 lg:col-span-5">
              <Link to="/docs#quickstart" className="btn-raw">
                QUICK_START
              </Link>
              <Link to="/about" className="btn-raw">
                WHY_THIS_EXISTS
              </Link>
              <a href={GITHUB_URL} className="btn-raw" target="_blank" rel="noopener noreferrer">
                GITHUB
              </a>
            </div>
          </div>
        </section>
      </div>
    </SiteLayout>
  )
}
