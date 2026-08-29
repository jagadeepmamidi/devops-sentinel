import { Link } from 'react-router-dom'
import SiteLayout from '../components/site/SiteLayout'
import { GITHUB_URL } from '@/lib/site'

export default function Terms() {
  return (
    <SiteLayout>
      <article className="site-grid py-12">
        <div className="col-span-full mx-auto grid w-full max-w-3xl gap-8">
          <div>
            <p className="section-kicker">Terms</p>
            <h1 className="text-[clamp(1.8rem,4vw,3.2rem)] font-extrabold leading-none tracking-[-0.02em]">
              Terms of use
            </h1>
            <p className="mt-2 text-[12px] text-muted-foreground">Last updated: August 27, 2026</p>
          </div>
          <p className="readable text-muted-foreground">
            DevOps Sentinel is open source software under the MIT License. You run the CLI, optional
            API, and optional operator UI yourself. These terms cover use of the public website and
            the published package.
          </p>
          <section>
            <h2 className="font-bold tracking-tight">Software</h2>
            <p className="readable mt-3 text-muted-foreground">
              The code is provided &quot;as is&quot;, without warranty. You are responsible for monitoring
              only systems you are authorized to monitor, for securing your Supabase project and API
              keys, and for any automation you approve.
            </p>
          </section>
          <section>
            <h2 className="font-bold tracking-tight">Acceptable use</h2>
            <ul className="data-list readable mt-3 text-muted-foreground">
              <li>Do not use Sentinel to attack, scan, or overwhelm systems you do not operate.</li>
              <li>Do not submit secrets in public GitHub issues or website forms.</li>
              <li>
                Do not represent Sentinel-hosted storage as a product feature. We do not host your
                data.
              </li>
            </ul>
          </section>
          <section>
            <h2 className="font-bold tracking-tight">Contact</h2>
            <p className="readable mt-3 text-muted-foreground">
              Questions:{' '}
              <a className="hud-link px-1 text-foreground" href={`${GITHUB_URL}/issues`}>
                GitHub issues
              </a>{' '}
              <Link className="hud-link px-1 text-foreground" to="/privacy">
                Privacy
              </Link>
              .
            </p>
          </section>
        </div>
      </article>
    </SiteLayout>
  )
}
