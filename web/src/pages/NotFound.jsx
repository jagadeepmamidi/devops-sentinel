import { Link } from 'react-router-dom'
import SiteLayout from '../components/site/SiteLayout'
import { Button } from '@/components/ui/button'

export default function NotFound() {
  return (
    <SiteLayout>
      <div className="mx-auto grid w-full max-w-lg gap-4 px-4 py-20 sm:px-6">
        <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">404</p>
        <h1 className="text-3xl font-medium tracking-tight">That route is not part of Sentinel</h1>
        <p className="text-sm leading-6 text-muted-foreground">
          The public site is docs, privacy, CLI auth, and an optional operator console. If a button
          sent you here, it is a bug - use the links below.
        </p>
        <div className="flex flex-wrap gap-3">
          <Button asChild>
            <Link to="/">Home</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/docs">Docs</Link>
          </Button>
        </div>
      </div>
    </SiteLayout>
  )
}
