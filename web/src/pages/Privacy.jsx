import { Link } from 'react-router-dom'
import SiteLayout from '../components/site/SiteLayout'
import { GITHUB_URL } from '@/lib/site'

export default function Privacy() {
  return (
    <SiteLayout>
      <article className="site-grid py-12">
        <div className="col-span-full mx-auto grid w-full max-w-3xl gap-8">
          <div>
            <p className="section-kicker">Privacy</p>
            <h1 className="text-[clamp(1.8rem,4vw,3.2rem)] font-extrabold leading-none tracking-[-0.02em]">
              Privacy policy
            </h1>
            <p className="mt-2 text-[12px] text-muted-foreground">Last updated: August 27, 2026</p>
          </div>
          <p className="readable text-muted-foreground">
            DevOps Sentinel is designed so we do not hold your operational data. Local mode writes
            SQLite on the machine that runs the CLI. Team mode writes to a Supabase project you
            create and control. The public website is documentation, CLI auth helper pages, and an
            optional operator UI that talks to an API you run.
          </p>
          <section>
            <h2 className="font-bold tracking-tight">What stays with you</h2>
            <ul className="data-list readable mt-3 text-muted-foreground">
              <li>Service URLs, health checks, latency, status codes, SSL metadata</li>
              <li>Incident records, timelines, response plans, postmortems</li>
              <li>Optional AI provider keys stored in ~/.sentinel/config.json on your machine</li>
              <li>Supabase session tokens if you authenticate against your project</li>
            </ul>
          </section>
          <section>
            <h2 className="font-bold tracking-tight">What we process only if you opt in</h2>
            <p className="readable mt-3 text-muted-foreground">
              If you configure OpenRouter, OpenAI, or Anthropic, Sentinel sends compact incident
              context to that provider to draft explanations. Keys never leave your config store
              except as you send them to the provider you chose. Slack and other integrations are
              opt-in webhooks you configure.
            </p>
          </section>
          <section>
            <h2 className="font-bold tracking-tight">What we do not collect</h2>
            <p className="readable mt-3 text-muted-foreground">
              No product telemetry by default. No hosted customer database. This marketing site does
              not require cookies for tracking. Browser local storage is used only for operator
              tokens and your Supabase session when you use those pages.
            </p>
          </section>
          <section>
            <h2 className="font-bold tracking-tight">Your rights</h2>
            <p className="readable mt-3 text-muted-foreground">
              Delete the `.sentinel` directory, revoke keys, or drop your Supabase project at any
              time. For questions,{' '}
              <a className="hud-link px-1 text-foreground" href={`${GITHUB_URL}/issues`}>
                open a GitHub issue
              </a>{' '}
              without pasting secrets. See also the{' '}
              <Link className="hud-link px-1 text-foreground" to="/terms">
                terms
              </Link>
              .
            </p>
          </section>
        </div>
      </article>
    </SiteLayout>
  )
}
