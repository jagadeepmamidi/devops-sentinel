import { Link } from 'react-router-dom'
import SiteLayout from '../components/site/SiteLayout'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { GITHUB_ISSUES_URL } from '@/lib/site'

export default function Feedback() {
  return (
    <SiteLayout>
      <div className="mx-auto grid w-full max-w-2xl gap-6 px-4 py-12 sm:px-6">
        <div>
          <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            Feedback
          </p>
          <h1 className="mt-3 text-4xl font-medium tracking-tight">Tell us what broke or what to build</h1>
          <p className="mt-4 text-base leading-7 text-muted-foreground">
            There is no hosted feedback inbox. Issues go to GitHub so they are public, searchable,
            and actually tracked.
          </p>
        </div>
        <Card>
          <CardHeader>
            <CardTitle>Open a GitHub issue</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4">
            <p className="text-sm leading-6 text-muted-foreground">
              Use a bug report for broken commands or links, a feature request for CLI/agent work,
              and never paste API keys, tokens, or personal data.
            </p>
            <div className="flex flex-wrap gap-3">
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
          </CardContent>
        </Card>
      </div>
    </SiteLayout>
  )
}
