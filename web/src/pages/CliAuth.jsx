import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import SiteLayout from '../components/site/SiteLayout'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { createSupabaseClient } from '@/lib/supabase'

export default function CliAuth() {
  const [searchParams] = useSearchParams()
  const [email, setEmail] = useState('')
  const [session, setSession] = useState(null)
  const [emailSent, setEmailSent] = useState(false)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)

  const redirectUri =
    searchParams.get('redirect_uri') || `${window.location.origin}/cli-auth`
  const state = searchParams.get('state') || ''
  const supabaseUrl = searchParams.get('supabase_url') || ''
  const supabaseAnonKey =
    searchParams.get('supabase_anon_key') || searchParams.get('supabase_key') || ''

  const client = useMemo(
    () => createSupabaseClient(supabaseUrl, supabaseAnonKey),
    [supabaseUrl, supabaseAnonKey],
  )
  const hasProject = Boolean(client)

  useEffect(() => {
    if (!client) return undefined
    let active = true
    client.auth.getSession().then(({ data }) => {
      if (active && data.session) setSession(data.session)
    })
    const { data: listener } = client.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession)
    })
    return () => {
      active = false
      listener.subscription.unsubscribe()
    }
  }, [client])

  async function signInWithProvider(provider) {
    setError('')
    if (!client) {
      setError('This page authenticates against YOUR Supabase project. Run sentinel login from a project initialized with --mode supabase.')
      return
    }
    const { error: authError } = await client.auth.signInWithOAuth({
      provider,
      options: {
        redirectTo: redirectUri,
        queryParams: state ? { state } : undefined,
      },
    })
    if (authError) setError(authError.message)
  }

  async function sendMagicLink(event) {
    event.preventDefault()
    setError('')
    if (!client) {
      setError('Missing supabase_url and supabase_anon_key from the CLI callback.')
      return
    }
    const { error: authError } = await client.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: redirectUri },
    })
    if (authError) setError(authError.message)
    else setEmailSent(true)
  }

  async function copyDeviceCommand() {
    try {
      await navigator.clipboard.writeText('sentinel login --device')
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1600)
    } catch {
      setCopied(false)
    }
  }

  return (
    <SiteLayout>
      <div className="page-wrap grid gap-6 py-12 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <p className="text-xs text-muted-foreground">CLI auth helper</p>
            <CardTitle className="text-3xl font-semibold tracking-tight">
              Sign in to your Supabase, not ours
            </CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4">
            <p className="text-sm leading-6 text-muted-foreground">
              Sentinel does not host accounts. This page is opened by{' '}
              <code className="font-mono text-foreground">sentinel login</code> and uses the
              project URL and anon key from your CLI config.
            </p>

            {!hasProject && (
              <Alert>
                <AlertTitle>No project in this URL</AlertTitle>
                <AlertDescription>
                  Use local mode with <code className="font-mono">sentinel init</code>, or
                  initialize Supabase mode and run <code className="font-mono">sentinel login</code>{' '}
                  so this page receives your project parameters.
                </AlertDescription>
              </Alert>
            )}

            {hasProject && (
              <p className="truncate font-mono text-xs text-muted-foreground">
                Project: {supabaseUrl}
              </p>
            )}

            <div className="flex flex-wrap gap-3">
              <Button type="button" onClick={() => signInWithProvider('google')} disabled={!hasProject}>
                Continue with Google
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => signInWithProvider('github')}
                disabled={!hasProject}
              >
                Continue with GitHub
              </Button>
            </div>

            <form className="grid gap-2" onSubmit={sendMagicLink}>
              <Label htmlFor="auth-email">Email magic link</Label>
              <div className="flex flex-col gap-2 sm:flex-row">
                <Input
                  id="auth-email"
                  type="email"
                  required
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="you@company.com"
                  disabled={!hasProject}
                />
                <Button type="submit" variant="secondary" disabled={!hasProject}>
                  Send link
                </Button>
              </div>
            </form>

            {emailSent ? (
              <p className="text-sm text-primary" role="status">
                Check email for the sign-in link from your Supabase project.
              </p>
            ) : null}
            {error ? (
              <p className="text-sm text-destructive" role="alert">
                {error}
              </p>
            ) : null}
            {session ? (
              <p className="text-sm text-primary">
                Signed in as {session.user.email}. You can return to the terminal.
              </p>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Prefer local?</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4">
            <pre className="overflow-x-auto border border-border bg-card p-4 font-mono text-[13px] leading-6">{`$ sentinel init
$ sentinel login --local
$ sentinel services add my-api https://api.example.com/health
$ sentinel monitor my-api`}</pre>
            <p className="text-sm text-muted-foreground">
              SSH / no browser callback: device flow still uses your Supabase project.
            </p>
            <Button type="button" variant="outline" onClick={copyDeviceCommand}>
              {copied ? 'Copied' : 'Copy: sentinel login --device'}
            </Button>
            <Button asChild variant="ghost">
              <Link to="/docs#supabase">Read BYO Supabase docs</Link>
            </Button>
            <span className="sr-only" aria-live="polite">
              {copied ? 'Device login command copied.' : ''}
            </span>
          </CardContent>
        </Card>
      </div>
    </SiteLayout>
  )
}
