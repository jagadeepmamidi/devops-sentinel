import { Link } from 'react-router-dom'
import SiteLayout from '../components/site/SiteLayout'
import { Button } from '@/components/ui/button'
import { GITHUB_ISSUES_URL } from '@/lib/site'

export default function Feedback() {
  return (
    <SiteLayout>
      <div className="page-wrap grid max-w-2xl gap-6 py-12">
        <div>
          <h1 className="text-4xl font-semibold tracking-tight">
            Tell us what broke or what to build
          </h1>
          <p className="mt-4 text-base leading-7 text-muted-foreground">
            There is no hosted feedback inbox. Issues go to GitHub so they are public, searchable,
            and actually tracked.
          </p>
        </div>
        <section className="border border-border p-5">
          <h2 className="text-lg font-semibold tracking-tight">Open a GitHub issue</h2>
          <p className="mt-3 text-sm leading-6 text-muted-foreground">
            Use a bug report for broken commands or links, a feature request for CLI/agent work,
            and never paste API keys, tokens, or personal data.
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <Button asChild>
              <a href={GITHUB_ISSUES_URL} target="_blank" rel="noopener noreferrer">
                New GitHub issue
              </a>
            </Button>
            <Button asChild variant="outline">
              <a href="mailto:jagadeep.mamidi@gmail.com">Email the maintainer</a>
            </Button>
            <Button asChild variant="ghost">
              <Link to="/docs">Back to docs</Link>
            </Button>
          </div>
        </section>
      </div>
    </SiteLayout>
  )
}
