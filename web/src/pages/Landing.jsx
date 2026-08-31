import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import AgentPipeline from '../components/site/AgentPipeline'
import CommandInstall from '../components/site/CommandInstall'
import LiveFailureDemo from '../components/site/LiveFailureDemo'
import SiteLayout from '../components/site/SiteLayout'
import TerminalReplay from '../components/site/TerminalReplay'
import { Button } from '@/components/ui/button'
import { PYPI_URL } from '@/lib/site'

const FEATURES = [
  {
    command: 'sentinel init',
    title: 'CLI first',
    body: 'Install, init, monitor, and generate postmortems without a hosted account.',
  },
  {
    command: '.sentinel/sentinel.db',
    title: 'Your store',
    body: 'Local SQLite, or connect the Supabase project you already own. Sentinel never keeps a copy.',
  },
  {
    command: 'human approval',
    title: 'No silent remediations',
    body: 'The CLI opens incidents and drafts postmortems. It does not mutate infrastructure on its own.',
  },
]

const HEALTH_ROWS = [
  { name: 'api-gateway', url: '/health', latency: '84 ms', status: 'Healthy' },
  { name: 'checkout-worker', url: '/ready', latency: '112 ms', status: 'Healthy' },
  { name: 'edge-cache', url: '/ping', latency: '96 ms', status: 'Watching' },
]

export default function Landing() {
  return (
    <SiteLayout>
      <div className="page-wrap pb-24">
        <section className="grid items-center gap-10 pt-10 pb-16 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)] lg:pt-14 lg:pb-20">
          <div className="max-w-xl">
            <h1 className="text-4xl font-semibold tracking-tight text-balance sm:text-5xl lg:text-[3.4rem] lg:leading-[1.05]">
              Watch the endpoint. Keep the incident in your own store.
            </h1>
            <p className="mt-5 max-w-[36ch] text-base leading-7 text-muted-foreground">
              Local-first health checks, incident memory, and labeled postmortems. SQLite by default.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Button asChild>
                <Link to="/docs#quickstart">
                  Get started
                  <ArrowRight className="size-4" />
                </Link>
              </Button>
              <Button asChild variant="outline">
                <Link to="/docs#agents">See the response stages</Link>
              </Button>
              <Button asChild variant="outline">
                <a href="#live-demo">Try a live 503</a>
              </Button>
            </div>
            <div className="mt-6">
              <CommandInstall />
            </div>
          </div>
          <TerminalReplay />
        </section>

        <section className="border-t border-border py-20">
          <h2 className="max-w-[18ch] text-3xl font-semibold tracking-tight">
            On-call stays in the terminal. Evidence stays yours.
          </h2>
          <p className="mt-4 max-w-[58ch] text-sm leading-7 text-muted-foreground">
            Hosted SRE platforms ask you to ship telemetry into their cloud. Sentinel checks
            endpoints you already own, writes incident memory next to the repo or into a database
            you provision, and stops agents at human approval.
          </p>
          <div className="mt-10 grid gap-px border border-border bg-border md:grid-cols-2">
            <article className="bg-background p-6 md:row-span-2 md:flex md:flex-col md:justify-between">
              <div>
                <p className="font-mono text-xs text-primary">{FEATURES[0].command}</p>
                <h3 className="mt-3 text-2xl font-semibold tracking-tight">{FEATURES[0].title}</h3>
                <p className="mt-2 max-w-[36ch] text-sm leading-6 text-muted-foreground">
                  {FEATURES[0].body}
                </p>
              </div>
            </article>
            {FEATURES.slice(1).map((item) => (
              <article key={item.title} className="bg-background p-6">
                <p className="font-mono text-xs text-primary">{item.command}</p>
                <h3 className="mt-3 text-lg font-semibold tracking-tight">{item.title}</h3>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.body}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="grid items-start gap-12 border-t border-border py-20 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
          <div>
            <h2 className="text-3xl font-semibold tracking-tight">Detect, open, plan. Humans still decide.</h2>
            <p className="mt-4 max-w-[42ch] text-sm leading-7 text-muted-foreground">
              These are CLI pipeline stages, not a separate multi-agent runtime. Sentinel records
              evidence and drafts a postmortem. It does not change infrastructure on its own.
            </p>
          </div>
          <AgentPipeline />
        </section>

        <section className="grid items-center gap-10 border-t border-border py-20 lg:grid-cols-2">
          <div>
            <h2 className="text-3xl font-semibold tracking-tight">
              Local by default. Supabase only if you bring it.
            </h2>
            <p className="mt-4 max-w-md text-sm leading-7 text-muted-foreground">
              <code className="text-foreground">sentinel init</code> writes SQLite under{' '}
              <code className="text-foreground">.sentinel/</code>. Team mode is{' '}
              <code className="text-foreground">sentinel init --mode supabase</code> against your
              project URL and anon key. Auth, incidents, and postmortems stay in that project.
            </p>
            <div className="mt-5 flex flex-wrap gap-3">
              <Button asChild variant="outline">
                <Link to="/docs#local">Local mode</Link>
              </Button>
              <Button asChild variant="outline">
                <Link to="/docs#supabase">Bring your Supabase</Link>
              </Button>
            </div>
          </div>
          <TerminalReplay
            title="sentinel init"
            meta="local"
            lines={[
              { tone: 'dim', text: '$ sentinel init' },
              { tone: 'ok', text: 'wrote .sentinel/sentinel.db' },
              { tone: 'ok', text: 'identity local@localhost' },
              { tone: 'dim', text: '$ sentinel demo' },
              { tone: 'warn', text: 'opened incident on /fail (HTTP 503)' },
              { tone: 'ok', text: 'next: sentinel incidents show <id>' },
            ]}
          />
        </section>

        <section className="border-t border-border py-20">
          <h2 className="text-3xl font-semibold tracking-tight">
            Continuous checks, not a dashboard you babysit
          </h2>
          <p className="mt-3 max-w-[55ch] text-sm leading-7 text-muted-foreground">
            HTTP 2xx and 3xx count as reachable. Failure and recovery thresholds keep a single blip
            from opening or closing an incident.
          </p>
          <div className="mt-8 overflow-x-auto border border-border">
            <table className="w-full min-w-[480px] text-left text-sm">
              <thead className="border-b border-border text-xs text-muted-foreground">
                <tr>
                  <th className="px-4 py-3 font-medium">Service</th>
                  <th className="px-4 py-3 font-medium">Path</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Latency</th>
                </tr>
              </thead>
              <tbody>
                {HEALTH_ROWS.map((row) => (
                  <tr key={row.name} className="border-b border-border last:border-0">
                    <td className="px-4 py-3 font-mono text-xs">{row.name}</td>
                    <td className="px-4 py-3 font-mono text-xs text-muted-foreground">{row.url}</td>
                    <td className={`px-4 py-3 ${row.status === 'Watching' ? 'text-muted-foreground' : 'text-primary'}`}>
                      {row.status}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs tabular-nums text-muted-foreground">
                      {row.latency}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Button asChild variant="link" className="mt-4 h-auto px-0">
            <Link to="/docs#commands">CLI reference</Link>
          </Button>
        </section>

        <section id="live-demo" className="grid items-start gap-10 border-t border-border py-20 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
          <div>
            <h2 className="text-3xl font-semibold tracking-tight">
              Break this site. Watch it in your terminal.
            </h2>
            <p className="mt-4 max-w-[46ch] text-sm leading-7 text-muted-foreground">
              After <code className="text-foreground">pip install</code> and{' '}
              <code className="text-foreground">sentinel init</code>, point the CLI at the live
              probe on this page. It stays HTTP 200 until you press the button. Then it returns
              503 so <code className="text-foreground">sentinel monitor</code> can open an
              incident in the terminal you already have open.
            </p>
            <Button asChild variant="link" className="mt-4 h-auto px-0">
              <Link to="/docs#live-demo">Same walkthrough in the docs</Link>
            </Button>
          </div>
          <LiveFailureDemo />
        </section>

        <section className="flex flex-col gap-6 border-t border-border py-16 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight">
              Install once. Monitor from the terminal you already use.
            </h2>
            <div className="mt-5 max-w-lg">
              <CommandInstall />
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button asChild variant="outline">
              <a href={PYPI_URL} target="_blank" rel="noopener noreferrer">
                View on PyPI
              </a>
            </Button>
            <Button asChild variant="outline">
              <Link to="/about">Why this exists</Link>
            </Button>
          </div>
        </section>
      </div>
    </SiteLayout>
  )
}
