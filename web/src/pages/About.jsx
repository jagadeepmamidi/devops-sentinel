import { Link } from 'react-router-dom'
import SiteLayout from '../components/site/SiteLayout'
import { Button } from '@/components/ui/button'
import { GITHUB_URL, PYPI_URL } from '@/lib/site'

export default function About() {
  return (
    <SiteLayout>
      <div className="page-wrap grid max-w-3xl gap-8 py-12">
        <div>
          <h1 className="text-4xl font-semibold tracking-tight">
            On-call should stay in the terminal, and the evidence should stay yours.
          </h1>
          <p className="mt-4 max-w-[62ch] text-base leading-7 text-muted-foreground">
            Most SRE platforms ask you to ship telemetry into their cloud. DevOps Sentinel is the
            opposite: a PyPI CLI that checks endpoints you already own, writes incident memory next
            to the repo or into a database you provision, and coordinates agents that stop at human
            approval.
          </p>
        </div>

        <section className="border border-border p-5">
          <h2 className="text-lg font-semibold tracking-tight">Business logic</h2>
          <div className="mt-4 grid gap-3 text-sm leading-7 text-muted-foreground">
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
          <h2 className="text-lg font-semibold tracking-tight">What we will not do</h2>
          <ul className="mt-4 grid gap-2 text-sm leading-7 text-muted-foreground">
            <li>Host your incident database or sell access to it.</li>
            <li>Require an account before `pip install` works.</li>
            <li>Let agents mutate infrastructure without a human.</li>
            <li>Hide the workflow behind a waitlist or a fake console.</li>
          </ul>
        </section>

        <div className="flex flex-wrap gap-3">
          <Button asChild>
            <Link to="/docs#quickstart">Read the quick start</Link>
          </Button>
          <Button asChild variant="outline">
            <a href={PYPI_URL} target="_blank" rel="noopener noreferrer">
              PyPI
            </a>
          </Button>
          <Button asChild variant="outline">
            <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer">
              GitHub
            </a>
          </Button>
          <Button asChild variant="outline">
            <a href="mailto:jagadeep.mamidi@gmail.com">jagadeep.mamidi@gmail.com</a>
          </Button>
        </div>
      </div>
    </SiteLayout>
  )
}
