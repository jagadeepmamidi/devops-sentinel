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

export default function OperatorServices() {
  const [tokenInput, setTokenInput] = useState(() => loadOperatorToken())
  const [services, setServices] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const token = loadOperatorToken()

  useEffect(() => {
    if (!token) {
      setServices([])
      return undefined
    }
    let cancelled = false
    setLoading(true)
    setError('')
    operatorFetch('/api/services', token)
      .then((payload) => {
        if (!cancelled) setServices(payload.services || [])
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message)
          setServices([])
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
      title="Services"
      description="Inspect services registered in the API you are running. Paste a bearer token from that API session."
      tokenInput={tokenInput}
      setTokenInput={setTokenInput}
      error={error}
      extraActions={
        <Link className="text-sm text-foreground underline" to="/operator/incidents">
          View incidents
        </Link>
      }
    >
      <Card>
        <CardHeader>
          <CardTitle>Registered services</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? <p className="text-sm text-muted-foreground">Loading services…</p> : null}
          {!loading && !token ? (
            <p className="text-sm text-muted-foreground">Save a token to load services.</p>
          ) : null}
          {!loading && token && services.length === 0 && !error ? (
            <p className="text-sm text-muted-foreground">No services found for this account.</p>
          ) : null}
          {services.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Interval</TableHead>
                  <TableHead>Last check</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {services.map((service) => (
                  <TableRow key={service.id}>
                    <TableCell>
                      <p className="font-medium">{service.name}</p>
                      <a
                        className="break-all text-xs text-muted-foreground underline"
                        href={service.url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        {service.url}
                      </a>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{service.last_status || 'unknown'}</Badge>
                    </TableCell>
                    <TableCell>{service.check_interval}s</TableCell>
                    <TableCell>{service.last_checked_at || 'Never'}</TableCell>
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
