import { lazy, Suspense } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import AgentPipeline from '../components/site/AgentPipeline'
import CommandInstall from '../components/site/CommandInstall'
import Reveal from '../components/site/Reveal'
import SiteLayout from '../components/site/SiteLayout'
import TerminalReplay from '../components/site/TerminalReplay'
import { Button } from '@/components/ui/button'

const OrbitalScene = lazy(() => import('../components/site/OrbitalScene'))

const FEATURES = [
  {
    title: 'CLI first',
    body: 'Install, init, monitor, and write postmortems without a hosted account.',
    span: 'md:col-span-2',
    visual: true,
  },
  {
    title: 'Your store',
    body: 'SQLite on disk, or the Supabase project you already own. Sentinel never keeps a copy.',
    span: '',
    visual: false,
  },
  {
    title: 'Safe agents',
    body: 'Agents propose the next move. Anything with side effects waits for a human.',
    span: '',
    visual: false,
  },
]

export default function Landing() {
  return (
    <SiteLayout>
      <div className="mx-auto w-full max-w-6xl px-4 pb-24 sm:px-6">
        <section className="grid items-center gap-10 py-8 lg:min-h-[100dvh] lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)] lg:py-12">
          <div className="max-w-xl">
            <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
              Local-first SRE
            </p>
            <h1 className="mt-4 text-4xl font-medium tracking-tighter text-balance sm:text-5xl lg:text-6xl lg:leading-[1.05]">
              Watch the endpoint. Keep the incident local.
            </h1>
            <p className="mt-4 max-w-[65ch] text-base leading-relaxed text-muted-foreground">
              HTTP checks, incident memory, and postmortems in SQLite. Optional login against your
              Supabase.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Button asChild>
                <Link to="/docs#quickstart">
                  Get started
                  <span className="grid size-7 place-items-center rounded-full bg-primary-foreground/10">
                    <ArrowRight className="size-3.5" />
                  </span>
                </Link>
              </Button>
              <Button asChild variant="outline">
                <Link to="/docs#demo">Run demo</Link>
              </Button>
            </div>
          </div>

          <div className="rounded-[1.5rem] border border-white/10 bg-white/[0.04] p-1.5">
            <div
              className="relative min-h-[300px] overflow-hidden rounded-[calc(1.5rem-6px)] bg-zinc-950 sm:min-h-[380px] lg:min-h-[420px]"
              aria-label="Chrome glass lens visualization"
            >
              <Suspense
                fallback={
                  <div className="absolute inset-0 grid place-items-center text-sm text-muted-foreground">
                    Loading lens
                  </div>
                }
              >
                <OrbitalScene />
              </Suspense>
            </div>
          </div>
        </section>

        <Reveal>
          <CommandInstall />
        </Reveal>

        <Reveal className="mt-20" delay={0.05}>
          <div className="grid gap-3 md:grid-cols-2">
            {FEATURES.map((item) => (
              <article
                key={item.title}
                className={`relative overflow-hidden rounded-2xl border border-white/10 bg-zinc-950/40 p-6 ${item.span}`.trim()}
              >
                {item.visual ? (
                  <img
                    src="/steel-instrument.webp"
                    alt="Brushed stainless instrument panel"
                    className="pointer-events-none absolute inset-0 h-full w-full object-cover opacity-35"
                  />
                ) : null}
                {item.visual ? (
                  <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-zinc-950 via-zinc-950/70 to-zinc-950/20" />
                ) : null}
                <div className="relative max-w-[65ch]">
                  <h2 className="text-xl font-medium tracking-tight">{item.title}</h2>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.body}</p>
                </div>
              </article>
            ))}
          </div>
        </Reveal>

        <Reveal className="mt-24" delay={0.08}>
          <AgentPipeline />
        </Reveal>

        <Reveal className="mt-24 grid gap-8" delay={0.08}>
          <div className="max-w-[65ch]">
            <h2 className="text-3xl font-medium tracking-tight text-balance">
              Local by default. Supabase only if you bring it.
            </h2>
            <p className="mt-4 text-sm leading-7 text-muted-foreground">
              <code className="font-mono text-[13px]">sentinel init</code> writes SQLite under{' '}
              <code className="font-mono text-[13px]">.sentinel/</code>. Team mode is{' '}
              <code className="font-mono text-[13px]">sentinel init --mode supabase</code> against
              your project URL and anon key.
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
        </Reveal>

        <Reveal className="mt-24" delay={0.05}>
          <div className="flex flex-col gap-6 rounded-2xl border border-white/10 bg-white/[0.03] px-6 py-8 sm:flex-row sm:items-center sm:justify-between">
            <h2 className="max-w-md text-2xl font-medium tracking-tight">
              Install once. Monitor from the terminal you already use.
            </h2>
            <Button asChild variant="outline">
              <Link to="/about">Why this exists</Link>
            </Button>
          </div>
        </Reveal>
      </div>
    </SiteLayout>
  )
}
