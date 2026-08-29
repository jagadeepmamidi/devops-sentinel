import { Link } from 'react-router-dom'
import SiteLayout from '../components/site/SiteLayout'
import { GITHUB_ISSUES_URL } from '@/lib/site'

export default function Feedback() {
  return (
    <SiteLayout>
      <div className="site-grid py-12">
        <article className="col-span-full mx-auto grid w-full max-w-2xl gap-8">
          <div>
            <p className="section-kicker">Feedback</p>
            <h1 className="max-w-[16ch] text-[clamp(1.8rem,4vw,3.2rem)] font-extrabold leading-none tracking-[-0.02em]">
              Tell us what broke or what to build
            </h1>
            <p className="readable mt-4 text-muted-foreground">
              There is no hosted feedback inbox. Issues go to GitHub so they are public, searchable,
              and actually tracked.
            </p>
          </div>
          <section className="border border-border p-5">
            <h2 className="font-bold tracking-tight">Open a GitHub issue</h2>
            <p className="readable mt-3 text-muted-foreground">
              Use a bug report for broken commands or links, a feature request for CLI/agent work,
              and never paste API keys, tokens, or personal data.
            </p>
            <div className="mt-5 flex flex-wrap gap-3">
              <a href={GITHUB_ISSUES_URL} className="btn-raw" target="_blank" rel="noopener noreferrer">
                NEW_ISSUE
              </a>
              <a href="mailto:jagadeep.mamidi@gmail.com" className="btn-raw">
                EMAIL
              </a>
              <Link to="/docs" className="btn-raw">
                DOCS
              </Link>
            </div>
          </section>
        </article>
      </div>
    </SiteLayout>
  )
}
