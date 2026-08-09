import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import SiteFooter from '../components/site/SiteFooter'
import SiteTopNav from '../components/site/SiteTopNav'
import { loadOperatorToken, operatorFetch, saveOperatorToken } from '../lib/operatorApi'
import './Operator.css'

const NAV_LINKS = [
  { to: '/operator/services', label: 'Services' },
  { to: '/operator/incidents', label: 'Incidents' },
  { to: '/docs', label: 'Docs' },
]

const FOOTER_LINKS = [
  { to: '/privacy', label: 'Privacy' },
  { to: '/terms', label: 'Terms' },
]

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
      return
    }

    let cancelled = false
    setLoading(true)
    setError('')

    operatorFetch(`/api/incidents/${incidentId}`, token)
      .then((payload) => {
        if (!cancelled) {
          setIncident(payload)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message)
          setIncident(null)
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [incidentId, token])

  async function handleGenerate(event) {
    event.preventDefault()
    if (!token || !incidentId) {
      return
    }

    setGenerating(true)
    setError('')
    try {
      const payload = await operatorFetch('/api/postmortems/generate', token, {
        method: 'POST',
        body: JSON.stringify({ incident_id: incidentId, resolution_notes: resolutionNotes }),
      })
      setIncident((previous) => (previous ? { ...previous, postmortem: payload.postmortem } : previous))
    } catch (err) {
      setError(err.message)
    } finally {
      setGenerating(false)
    }
  }

  function handleSaveToken(event) {
    event.preventDefault()
    saveOperatorToken(tokenInput.trim())
    setError('')
  }

  return (
    <div className="site-page">
      <a className="site-skip-link" href="#operator-main">Skip to content</a>
      <SiteTopNav links={NAV_LINKS} brandTo="/" />

      <main id="operator-main" className="site-main site-container operator-main">
        <div className="operator-stack">
          <section className="site-card operator-panel">
            <p className="site-label">Operator Console</p>
            <h1 className="site-title">Incident Detail</h1>
            <p className="site-text">
              Inspect a single incident and generate a postmortem directly from the API.
            </p>

            <form className="operator-token-form" onSubmit={handleSaveToken}>
              <input
                type="password"
                value={tokenInput}
                onChange={(event) => setTokenInput(event.target.value)}
                placeholder="Paste bearer token"
                aria-label="Bearer token"
              />
              <button className="site-btn primary" type="submit">Save token</button>
              <Link className="site-btn secondary" to="/operator/incidents">Back to incidents</Link>
            </form>
            {error ? <p className="operator-error">{error}</p> : null}
          </section>

          <section className="site-card operator-panel">
            {loading ? <p className="site-text">Loading incident...</p> : null}
            {!loading && !token ? <p className="operator-empty">Save a token to load incident data.</p> : null}
            {!loading && incident ? (
              <>
                <h2>{incident.service_name || incident.service_id}</h2>
                <p className="site-text">{incident.error_message || 'No error summary recorded.'}</p>

                <div className="operator-detail-grid">
                  <article className="site-card soft operator-detail-card">
                    <span>Status</span>
                    <strong>{incident.status}</strong>
                  </article>
                  <article className="site-card soft operator-detail-card">
                    <span>Severity</span>
                    <strong>{incident.severity}</strong>
                  </article>
                  <article className="site-card soft operator-detail-card">
                    <span>Detected</span>
                    <strong>{incident.detected_at || 'Unknown'}</strong>
                  </article>
                  <article className="site-card soft operator-detail-card">
                    <span>Resolved</span>
                    <strong>{incident.resolved_at || 'Still open'}</strong>
                  </article>
                </div>

                <form className="operator-generate-form" onSubmit={handleGenerate}>
                  <label htmlFor="resolutionNotes">Resolution notes</label>
                  <textarea
                    id="resolutionNotes"
                    rows="4"
                    value={resolutionNotes}
                    onChange={(event) => setResolutionNotes(event.target.value)}
                    placeholder="Optional context to include in the generated postmortem"
                  />
                  <button className="site-btn primary" type="submit" disabled={generating}>
                    {generating ? 'Generating...' : 'Generate postmortem'}
                  </button>
                </form>

                <div className="site-card soft operator-panel">
                  <h3>Postmortem</h3>
                  <div className="operator-markdown">
                    {incident.postmortem || 'No postmortem generated yet.'}
                  </div>
                </div>
              </>
            ) : null}
          </section>
        </div>
      </main>

      <SiteFooter links={FOOTER_LINKS} text="DevOps Sentinel incident detail" />
    </div>
  )
}
