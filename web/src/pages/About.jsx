import { Link } from 'react-router-dom'
import SiteLayout from '../components/site/SiteLayout'
import { Button } from '@/components/ui/button'
import { GITHUB_URL } from '@/lib/site'

const FACTS = [
  ['Goal', 'Shorten time-to-signal and time-to-context without becoming another SaaS that holds production data.'],
  ['Product', 'Health checks, thresholded incidents, a four-role agent loop, postmortems, MCP for AI operators, optional Slack.'],
  ['Trust model', 'Local SQLite is enough. Supabase is compatibility for teams that already run it: bring-your-own, never ours.'],
  ['Safety', 'Agents explain and propose. Destructive remediation is an explicit approval, not a default.'],
]

const WONT = [
  'Host your incident database or sell access to it.',
  'Require an account before pip install works.',
  'Let agents mutate infrastructure without a human.',
  'Hide the workflow behind a waitlist or a fake console.',
]

export default function About() {
  return (
    <SiteLayout>
      <div className="mx-auto grid w-full max-w-3xl gap-14 px-4 py-16 sm:px-6">
        <div>
          <h1 className="max-w-[16ch] text-4xl font-medium tracking-tight text-balance sm:text-5xl">
            On-call should stay in the terminal, and the evidence should stay yours.
          </h1>
          <p className="mt-5 max-w-[65ch] text-base leading-7 text-muted-foreground">
            Most SRE platforms ask you to ship telemetry into their cloud. DevOps Sentinel is the
            opposite: a PyPI CLI that checks endpoints you already own, writes incident memory next
            to the repo or into a database you provision, and coordinates agents that stop at human
            approval.
          </p>
        </div>

        <dl className="divide-y divide-white/8 border-y border-white/8">
          {FACTS.map(([label, body]) => (
            <div key={label} className="grid gap-2 py-5 sm:grid-cols-[8rem_minmax(0,1fr)] sm:gap-8">
              <dt className="text-sm font-medium text-foreground">{label}</dt>
              <dd className="text-sm leading-7 text-muted-foreground">{body}</dd>
            </div>
          ))}
        </dl>

        <div>
          <h2 className="text-2xl font-medium tracking-tight">What we will not do</h2>
          <ul className="mt-5 grid gap-3 text-sm leading-7 text-muted-foreground">
            {WONT.map((item) => (
              <li key={item} className="border-l border-white/12 pl-4">
                {item}
              </li>
            ))}
          </ul>
        </div>

        <div className="flex flex-wrap gap-3">
          <Button asChild>
            <Link to="/docs#quickstart">Read the quick start</Link>
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
