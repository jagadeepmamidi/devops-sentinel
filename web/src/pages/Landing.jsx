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

export default function Landing() {
  return (
    <SiteLayout>
      <div className="mx-auto w-full max-w-6xl px-4 pb-28 sm:px-6">
        <section className="grid items-center gap-8 pt-6 pb-4 lg:min-h-[calc(100dvh-5.5rem)] lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)] lg:gap-10 lg:pt-8 lg:pb-10">
          <div className="relative z-10 max-w-xl">
            <h1 className="max-w-[13ch] text-4xl font-medium tracking-tighter text-balance sm:text-5xl lg:text-6xl lg:leading-[1.05]">
              Watch the endpoint. Keep the incident local.
            </h1>
            <p className="mt-4 max-w-[36ch] text-base leading-relaxed text-muted-foreground">
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

          <div className="relative lg:translate-y-6">
            <div className="rounded-[1.5rem] border border-white/10 bg-white/[0.04] p-1.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]">
              <div
                className="relative min-h-[280px] overflow-hidden rounded-[calc(1.5rem-6px)] bg-zinc-950 sm:min-h-[360px] lg:min-h-[420px]"
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
          </div>
        </section>

        <Reveal>
          <CommandInstall />
        </Reveal>

        <Reveal className="mt-16 lg:-mt-2" delay={0.05}>
          <div className="grid gap-3 lg:grid-cols-12">
            <article className="relative min-h-[240px] overflow-hidden rounded-[1.75rem] border border-white/10 bg-zinc-950 lg:col-span-7 lg:row-span-2 lg:min-h-[420px]">
              <img
                src="/steel-instrument.webp"
                alt="Brushed stainless instrument panel"
                className="pointer-events-none absolute inset-0 h-full w-full object-cover opacity-45 mix-blend-luminosity"
              />
              <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-zinc-950 via-zinc-950/55 to-zinc-950/15" />
              <div className="relative flex h-full min-h-[240px] flex-col justify-end p-6 lg:min-h-[420px] lg:p-8">
                <h2 className="text-xl font-medium tracking-tight">CLI first</h2>
                <p className="mt-2 max-w-[42ch] text-sm leading-6 text-muted-foreground">
                  Install, init, monitor, and write postmortems without a hosted account.
                </p>
              </div>
            </article>

            <article className="rounded-[1.75rem] border border-white/8 bg-[radial-gradient(120%_90%_at_0%_0%,rgba(255,255,255,0.07),transparent_55%),linear-gradient(180deg,rgba(18,18,20,0.92),rgba(8,8,10,0.96))] p-6 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)] lg:col-span-5">
              <h2 className="text-xl font-medium tracking-tight">Your store</h2>
              <dl className="mt-5 space-y-3 text-sm">
                <div className="flex items-baseline justify-between gap-4 border-b border-white/8 pb-3">
                  <dt className="text-zinc-200">Local</dt>
                  <dd className="text-right text-muted-foreground">SQLite on disk. Default.</dd>
                </div>
                <div className="flex items-baseline justify-between gap-4">
                  <dt className="text-zinc-200">Your cloud</dt>
                  <dd className="text-right text-muted-foreground">Bring a Supabase project.</dd>
                </div>
              </dl>
            </article>

            <aside className="rounded-[1.75rem] border border-dashed border-white/14 bg-transparent px-6 py-5 lg:col-span-5">
              <h2 className="text-xl font-medium tracking-tight">Safe agents</h2>
              <p className="mt-2 max-w-[42ch] text-sm leading-6 text-muted-foreground">
                Agents propose the next move. Anything with side effects waits for a human.
              </p>
            </aside>
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

        <Reveal className="mt-28" delay={0.05}>
          <div className="flex flex-col gap-5 border-t border-white/10 pt-10 sm:flex-row sm:items-center sm:justify-between">
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
