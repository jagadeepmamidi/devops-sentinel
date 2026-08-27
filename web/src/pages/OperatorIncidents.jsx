import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import OperatorShell from '../components/site/OperatorShell'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { loadOperatorToken, operatorFetch } from '@/lib/operatorApi'

export default function OperatorIncidents() {
  const [tokenInput, setTokenInput] = useState(() => loadOperatorToken())
  const [incidents, setIncidents] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const token = loadOperatorToken()

  useEffect(() => {
    if (!token) {
      return undefined
    }

    let cancelled = false
    Promise.resolve()
      .then(() => {
        if (!cancelled) {
          setLoading(true)
          setError('')
        }
        return operatorFetch('/api/incidents', token)
      })
      .then((payload) => {
        if (!cancelled) setIncidents(payload.incidents || [])
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message)
          setIncidents([])
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [token])

  return (
    <OperatorShell
      title="Incidents"
      description="Browse incidents stored by the API you are running."
      tokenInput={tokenInput}
      setTokenInput={setTokenInput}
      error={error}
      extraActions={
        <Link className="text-sm text-foreground underline" to="/operator/services">
          View services
        </Link>
      }
    >
      <Card>
        <CardHeader>
          <CardTitle>Incident list</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? <p className="text-sm text-muted-foreground">Loading incidents…</p> : null}
          {!loading && !token ? (
            <p className="text-sm text-muted-foreground">Save a token to load incidents.</p>
          ) : null}
          {!loading && token && incidents.length === 0 && !error ? (
            <p className="text-sm text-muted-foreground">No incidents found.</p>
          ) : null}
          {incidents.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Service</TableHead>
                  <TableHead>Severity</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Detected</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {incidents.map((incident) => (
                  <TableRow key={incident.id}>
                    <TableCell>
                      <Link
                        className="font-medium underline"
                        to={`/operator/incidents/${incident.id}`}
                      >
                        {incident.service_name || incident.service_id || incident.id}
                      </Link>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{incident.severity}</Badge>
                    </TableCell>
                    <TableCell>{incident.status}</TableCell>
                    <TableCell>{incident.detected_at || 'Unknown'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : null}
        </CardContent>
      </Card>
    </OperatorShell>
  )
}
