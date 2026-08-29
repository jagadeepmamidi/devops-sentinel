import { Link } from 'react-router-dom'
import SiteLayout from '../components/site/SiteLayout'
import { GITHUB_URL } from '@/lib/site'

export default function About() {
  return (
    <SiteLayout>
      <div className="site-grid py-12">
        <article className="col-span-full mx-auto grid w-full max-w-3xl gap-8">
          <div>
            <p className="section-kicker">Why Sentinel exists</p>
            <h1 className="max-w-[18ch] text-[clamp(1.8rem,4vw,3.2rem)] font-extrabold leading-none tracking-[-0.02em]">
              On-call should stay in the terminal, and the evidence should stay yours.
            </h1>
            <p className="readable mt-4 text-muted-foreground">
              Most SRE platforms ask you to ship telemetry into their cloud. DevOps Sentinel is the
              opposite: a PyPI CLI that checks endpoints you already own, writes incident memory next
              to the repo or into a database you provision, and coordinates agents that stop at human
              approval.
            </p>
          </div>

          <section className="border border-border p-5">
            <h2 className="font-bold tracking-tight">Business logic</h2>
            <div className="readable mt-4 grid gap-3 text-muted-foreground">
              <p>
                <strong className="text-foreground">Goal:</strong> shorten time-to-signal and
                time-to-context without becoming another SaaS that holds production data.
              </p>
              <p>
                <strong className="text-foreground">Product:</strong> health checks, thresholded
                incidents, a four-role agent loop, postmortems, MCP for AI operators, optional Slack.
              </p>
              <p>
                <strong className="text-foreground">Trust model:</strong> local SQLite is enough.
                Supabase is compatibility for teams that already run it. Bring-your-own, never ours.
              </p>
              <p>
                <strong className="text-foreground">Safety:</strong> agents explain and propose.
                Destructive remediation is an explicit approval, not a default.
              </p>
            </div>
          </section>

          <section className="border border-border p-5">
            <h2 className="font-bold tracking-tight">What we will not do</h2>
            <ul className="data-list readable mt-4 text-muted-foreground">
              <li>Host your incident database or sell access to it.</li>
              <li>Require an account before `pip install` works.</li>
              <li>Let agents mutate infrastructure without a human.</li>
              <li>Hide the workflow behind a waitlist or a fake console.</li>
            </ul>
          </section>

          <div className="flex flex-wrap gap-3">
            <Link to="/docs#quickstart" className="btn-raw">
              QUICK_START
            </Link>
            <a href={GITHUB_URL} className="btn-raw" target="_blank" rel="noopener noreferrer">
              GITHUB
            </a>
            <a href="mailto:jagadeep.mamidi@gmail.com" className="btn-raw">
              EMAIL
            </a>
          </div>
        </article>
      </div>
    </SiteLayout>
  )
}
