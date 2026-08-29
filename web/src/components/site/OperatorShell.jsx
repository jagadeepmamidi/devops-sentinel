import { useState } from 'react'
import { Link } from 'react-router-dom'
import SiteLayout from './SiteLayout'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { OPERATOR_NAV } from '@/lib/site'
import { saveOperatorToken } from '@/lib/operatorApi'

export default function OperatorShell({
  title,
  description,
  tokenInput,
  setTokenInput,
  error,
  children,
  extraActions,
}) {
  const [saved, setSaved] = useState(false)

  function handleSaveToken(event) {
    event.preventDefault()
    saveOperatorToken(tokenInput.trim())
    setSaved(true)
    window.setTimeout(() => setSaved(false), 1200)
  }

  return (
    <SiteLayout navLinks={OPERATOR_NAV}>
      <div className="site-grid py-10">
        <Card className="col-span-full">
          <CardHeader>
            <p className="section-kicker mb-2">Optional local console</p>
            <CardTitle className="text-[clamp(1.6rem,3vw,2.4rem)] font-extrabold leading-none tracking-[-0.02em]">
              {title}
            </CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4">
            <p className="readable text-muted-foreground">{description}</p>
            <Alert>
              <AlertDescription>
                This UI calls an API you run with <code className="font-mono">sentinel serve</code>.
                It is not a hosted Sentinel backend.
              </AlertDescription>
            </Alert>
            <form className="grid gap-2 sm:grid-cols-[minmax(0,1fr)_auto_auto]" onSubmit={handleSaveToken}>
              <div className="grid gap-2">
                <Label htmlFor="operator-token">Bearer token</Label>
                <Input
                  id="operator-token"
                  type="password"
                  value={tokenInput}
                  onChange={(event) => setTokenInput(event.target.value)}
                  placeholder="Paste bearer token from your API session"
                  autoComplete="off"
                  name="token"
                />
              </div>
              <Button type="submit" className="sm:self-end">
                {saved ? 'Saved' : 'Save token'}
              </Button>
              <Button
                type="button"
                variant="outline"
                className="sm:self-end"
                onClick={() => {
                  saveOperatorToken('')
                  setTokenInput('')
                }}
              >
                Clear
              </Button>
            </form>
            {extraActions}
            {error ? (
              <p className="text-[12px] text-destructive" role="alert">
                {error}
              </p>
            ) : null}
          </CardContent>
        </Card>
        <div className="col-span-full">{children}</div>
        <p className="col-span-full readable text-muted-foreground">
          Need the CLI instead?{' '}
          <Link className="hud-link px-1 text-foreground" to="/docs#quickstart">
            Open the quick start
          </Link>
          .
        </p>
      </div>
    </SiteLayout>
  )
}
