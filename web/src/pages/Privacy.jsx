import { Link } from 'react-router-dom'
import SiteLayout from '../components/site/SiteLayout'
import { GITHUB_URL } from '@/lib/site'

export default function Privacy() {
  return (
    <SiteLayout>
      <article className="mx-auto grid w-full max-w-3xl gap-6 px-4 py-12 sm:px-6">
        <div>
          <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            Privacy
          </p>
          <h1 className="mt-3 text-4xl font-medium tracking-tight">Privacy policy</h1>
          <p className="mt-2 text-sm text-muted-foreground">Last updated: August 27, 2026</p>
        </div>
        <p className="text-base leading-7 text-muted-foreground">
          DevOps Sentinel is designed so we do not hold your operational data. Local mode writes
          SQLite on the machine that runs the CLI. Team mode writes to a Supabase project you
          create and control. The public website is documentation, CLI auth helper pages, and an
          optional operator UI that talks to an API you run.
        </p>
        <section>
          <h2 className="text-xl font-medium">What stays with you</h2>
          <ul className="mt-3 grid gap-2 text-sm leading-7 text-muted-foreground">
            <li>Service URLs, health checks, latency, status codes, SSL metadata</li>
            <li>Incident records, timelines, response plans, postmortems</li>
            <li>Optional AI provider keys stored in ~/.sentinel/config.json on your machine</li>
            <li>Supabase session tokens if you authenticate against your project</li>
          </ul>
        </section>
        <section>
          <h2 className="text-xl font-medium">What we process only if you opt in</h2>
          <p className="mt-3 text-sm leading-7 text-muted-foreground">
            If you configure OpenRouter, OpenAI, or Anthropic, Sentinel sends compact incident
            context to that provider to draft explanations. Keys never leave your config store
            except as you send them to the provider you chose. Slack and other integrations are
            opt-in webhooks you configure.
          </p>
        </section>
        <section>
          <h2 className="text-xl font-medium">What we do not collect</h2>
          <p className="mt-3 text-sm leading-7 text-muted-foreground">
            No product telemetry by default. No hosted customer database. This marketing site does
            not require cookies for tracking. Browser local storage is used only for operator
            tokens and your Supabase session when you use those pages.
          </p>
        </section>
        <section>
          <h2 className="text-xl font-medium">Your rights</h2>
          <p className="mt-3 text-sm leading-7 text-muted-foreground">
            Delete the `.sentinel` directory, revoke keys, or drop your Supabase project at any
            time. For questions,{' '}
            <a className="text-foreground underline" href={`${GITHUB_URL}/issues`}>
              open a GitHub issue
            </a>{' '}
            without pasting secrets. See also the{' '}
            <Link className="text-foreground underline" to="/terms">
              terms
            </Link>
            .
          </p>
        </section>
      </article>
    </SiteLayout>
  )
}
