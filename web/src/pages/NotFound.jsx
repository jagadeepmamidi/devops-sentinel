import { Link } from 'react-router-dom'
import SiteLayout from '../components/site/SiteLayout'

export default function NotFound() {
  return (
    <SiteLayout>
      <div className="site-grid py-20">
        <div className="col-span-full mx-auto grid w-full max-w-lg gap-4">
          <p className="section-kicker">404</p>
          <h1 className="text-[clamp(1.6rem,4vw,2.4rem)] font-extrabold leading-none tracking-[-0.02em]">
            That route is not part of Sentinel
          </h1>
          <p className="readable text-muted-foreground">
            The public site is docs, privacy, CLI auth, and an optional operator console. If a button
            sent you here, it is a bug. Use the links below.
          </p>
          <div className="mt-2 flex flex-wrap gap-3">
            <Link to="/" className="btn-raw">
              HOME
            </Link>
            <Link to="/docs" className="btn-raw">
              DOCS
            </Link>
          </div>
        </div>
      </div>
    </SiteLayout>
  )
}
