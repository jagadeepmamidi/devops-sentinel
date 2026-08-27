import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import OperatorShell from '../components/site/OperatorShell'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { loadOperatorToken, operatorFetch } from '@/lib/operatorApi'

export default function OperatorIncidentDetail() {
  const { incidentId } = useParams()
  const [tokenInput, setTokenInput] = useState(() => loadOperatorToken())
  const [incident, setIncident] = useState(null)
  const [resolutionNotes, setResolutionNotes] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const token = loadOperatorToken()

  useEffect(() => {
    if (!token || !incidentId) {
      setIncident(null)
      return undefined
    }
    let cancelled = false
    setLoading(true)
    setError('')
    operatorFetch(`/api/incidents/${incidentId}`, token)
      .then((payload) => {
        if (!cancelled) setIncident(payload)
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message)
          setIncident(null)
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [incidentId, token])

  async function handleGenerate(event) {
    event.preventDefault()
    if (!token || !incidentId) return
    setGenerating(true)
    setError('')
    try {
      const payload = await operatorFetch('/api/postmortems/generate', token, {
        method: 'POST',
        body: JSON.stringify({
          incident_id: incidentId,
          resolution_notes: resolutionNotes,
        }),
      })
      setIncident((previous) =>
        previous ? { ...previous, postmortem: payload.postmortem } : previous,
      )
    } catch (err) {
      setError(err.message)
    } finally {
      setGenerating(false)
    }
  }

  return (
    <OperatorShell
      title="Incident detail"
      description="Inspect one incident from your local or self-hosted API and generate a postmortem."
      tokenInput={tokenInput}
      setTokenInput={setTokenInput}
      error={error}
      extraActions={
        <Link className="text-sm text-foreground underline" to="/operator/incidents">
          Back to incidents
        </Link>
      }
    >
      <Card>
        <CardHeader>
          <CardTitle>{incident?.service_name || incident?.service_id || 'Incident'}</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4">
          {loading ? <p className="text-sm text-muted-foreground">Loading incident…</p> : null}
          {!loading && !token ? (
            <p className="text-sm text-muted-foreground">Save a token to load incident data.</p>
          ) : null}
          {!loading && token && !incident && !error ? (
            <p className="text-sm text-muted-foreground">Incident not found.</p>
          ) : null}
          {incident ? (
            <>
              <p className="text-sm text-muted-foreground">
                {incident.error_message || 'No error summary recorded.'}
              </p>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                {[
                  ['Status', incident.status],
                  ['Severity', incident.severity],
                  ['Detected', incident.detected_at || 'Unknown'],
                  ['Resolved', incident.resolved_at || 'Still open'],
                ].map(([label, value]) => (
                  <div key={label} className="rounded-lg border border-border p-3">
                    <p className="text-xs text-muted-foreground">{label}</p>
                    <p className="mt-1 text-sm font-medium">{value}</p>
                  </div>
                ))}
              </div>
              <form className="grid gap-2" onSubmit={handleGenerate}>
                <Label htmlFor="resolutionNotes">Resolution notes</Label>
                <textarea
                  id="resolutionNotes"
                  rows="4"
                  value={resolutionNotes}
                  onChange={(event) => setResolutionNotes(event.target.value)}
                  placeholder="Optional context for generated postmortem…"
                  className="min-h-24 rounded-md border border-input bg-transparent px-3 py-2 text-sm"
                />
                <Button type="submit" disabled={generating} className="w-fit">
                  {generating ? 'Generating…' : 'Generate postmortem'}
                </Button>
              </form>
              <div className="rounded-lg border border-border bg-secondary/20 p-4">
                <h3 className="text-sm font-medium">Postmortem</h3>
                <pre className="mt-2 overflow-x-auto whitespace-pre-wrap font-mono text-xs leading-6">
                  {incident.postmortem || 'No postmortem generated yet.'}
                </pre>
              </div>
            </>
          ) : null}
        </CardContent>
      </Card>
    </OperatorShell>
  )
}
