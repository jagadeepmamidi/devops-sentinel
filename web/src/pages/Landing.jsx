import { lazy, Suspense } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, Database, Shield, Terminal } from 'lucide-react'
import AgentPipeline from '../components/site/AgentPipeline'
import CommandInstall from '../components/site/CommandInstall'
import SiteLayout from '../components/site/SiteLayout'
import TerminalReplay from '../components/site/TerminalReplay'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const OrbitalScene = lazy(() => import('../components/site/OrbitalScene'))

const healthRows = [
  { name: 'api-gateway', url: '/health', latency: '84 ms', status: 'Healthy' },
  { name: 'checkout-worker', url: '/ready', latency: '112 ms', status: 'Healthy' },
  { name: 'edge-cache', url: '/ping', latency: '96 ms', status: 'Watching' },
]

export default function Landing() {
  return (
    <SiteLayout>
      <div className="mx-auto w-full max-w-6xl px-4 pb-20 sm:px-6">
        <section className="grid items-center gap-10 py-10 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)] lg:py-16">
          <div className="max-w-xl">
            <Badge variant="outline" className="font-mono text-[10px] uppercase tracking-widest">
              Terminal-first SRE · v0.1.3
            </Badge>
            <h1 className="mt-5 text-4xl font-medium tracking-tight text-balance sm:text-5xl lg:text-6xl">
              Watch the endpoint. Keep the incident in your own store.
            </h1>
            <p className="mt-5 text-base leading-7 text-muted-foreground sm:text-lg">
              DevOps Sentinel is a local-first CLI for health checks, multi-agent incident
              response, and postmortems. SQLite by default. Optional login against{' '}
              <strong className="font-medium text-foreground">your</strong> Supabase project.
              We do not host or store your operational data.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Button asChild>
                <Link to="/docs#quickstart">
                  Get started
                  <ArrowRight className="size-4" />
                </Link>
              </Button>
              <Button asChild variant="outline">
                <Link to="/docs#agents">See the agent loop</Link>
              </Button>
            </div>
            <div className="mt-6">
              <CommandInstall />
            </div>
          </div>

          <div
            className="relative min-h-[360px] overflow-hidden rounded-xl border border-border bg-card sm:min-h-[420px]"
            aria-label="Service mesh visualization"
          >
            <div className="absolute inset-x-4 top-4 z-10 flex items-start justify-between gap-3">
              <div>
                <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                  Local mesh
                </p>
                <p className="text-sm font-medium">production-api · SQLite</p>
              </div>
              <Badge variant="secondary">Live demo</Badge>
            </div>
            <Suspense
              fallback={
                <div className="absolute inset-0 grid place-items-center text-sm text-muted-foreground">
                  Loading mesh…
                </div>
              }
            >
              <OrbitalScene />
            </Suspense>
            <p className="absolute inset-x-4 bottom-4 z-10 font-mono text-xs text-muted-foreground">
              Watcher · First Responder · Investigator · Strategist
            </p>
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-3">
          {[
            {
              icon: Terminal,
              title: 'CLI first',
              body: 'Install, init, monitor, and generate postmortems without a hosted account.',
            },
            {
              icon: Database,
              title: 'Your store',
              body: 'Local SQLite, or connect the Supabase project you already own. Sentinel never keeps a copy.',
            },
            {
              icon: Shield,
              title: 'Safe agents',
              body: 'Agents propose the next move. Anything with side effects waits for a human.',
            },
          ].map((item) => (
            <Card key={item.title} className="border-border">
              <CardHeader>
                <item.icon className="size-4 text-primary" />
                <CardTitle className="text-base">{item.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-6 text-muted-foreground">{item.body}</p>
              </CardContent>
            </Card>
          ))}
        </section>

        <section className="mt-16 grid gap-6 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
          <Card>
            <CardHeader>
              <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                Health surface
              </p>
              <CardTitle>Continuous checks, not a dashboard you babysit</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3">
              {healthRows.map((row) => (
                <div
                  key={row.name}
                  className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 border-t border-border pt-3 sm:grid-cols-[minmax(0,1.4fr)_auto_auto]"
                >
                  <div className="min-w-0">
                    <p className="truncate font-mono text-sm">{row.name}</p>
                    <p className="font-mono text-xs text-muted-foreground">{row.url}</p>
                  </div>
                  <Badge variant={row.status === 'Watching' ? 'outline' : 'secondary'}>
                    {row.status}
                  </Badge>
                  <span className="hidden font-mono text-xs text-muted-foreground sm:inline">
                    {row.latency}
                  </span>
                </div>
              ))}
              <Button asChild variant="link" className="h-auto justify-start px-0">
                <Link to="/docs#commands">CLI reference →</Link>
              </Button>
            </CardContent>
          </Card>
          <AgentPipeline />
        </section>

        <section className="mt-16 grid items-center gap-8 lg:grid-cols-2">
          <div>
            <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              Two ways to persist
            </p>
            <h2 className="mt-3 text-3xl font-medium tracking-tight">
              Local by default. Supabase only if you bring it.
            </h2>
            <p className="mt-4 max-w-md text-sm leading-7 text-muted-foreground">
              `sentinel init` writes SQLite under `.sentinel/`. Team mode is{' '}
              `sentinel init --mode supabase` against your project URL and anon key. Auth,
              incidents, and postmortems stay in that project.
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
          <TerminalReplay />
        </section>

        <Card className="mt-16">
          <CardContent className="flex flex-col gap-6 p-6 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                Next
              </p>
              <h2 className="mt-2 text-2xl font-medium tracking-tight">
                Install once. Monitor from the terminal you already use.
              </h2>
            </div>
            <div className="flex flex-wrap gap-3">
              <Button asChild>
                <Link to="/docs#quickstart">Open the quick start</Link>
              </Button>
              <Button asChild variant="outline">
                <Link to="/about">Why this exists</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </SiteLayout>
  )
}
