import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { supabase } from '../lib/supabase'
import Navbar from '../components/Navbar'
import './Incidents.css'

export default function Incidents() {
    const { user } = useAuth()
    const [incidents, setIncidents] = useState([])
    const [loading, setLoading] = useState(true)
    const [filter, setFilter] = useState('all')

    useEffect(() => {
        fetchIncidents()
    }, [user, filter])

    const fetchIncidents = async () => {
        if (!user) return

        let query = supabase
            .from('incidents')
            .select(`
        *,
        services (name, url)
      `)
            .order('detected_at', { ascending: false })

        if (filter !== 'all') {
            query = query.eq('status', filter)
        }

        const { data, error } = await query.limit(50)

        if (!error) setIncidents(data || [])
        setLoading(false)
    }

    const formatDuration = (seconds) => {
        if (!seconds) return '--'
        if (seconds < 60) return `${seconds.toFixed(1)}s`
        return `${(seconds / 60).toFixed(1)}m`
    }

    return (
        <div className="dashboard-layout">
            <Navbar />
            <main className="dashboard-main">
                <div className="page-header">
                    <h1>Incidents</h1>
                    <div className="filter-tabs">
                        {['all', 'detecting', 'alerting', 'investigating', 'resolved'].map(status => (
                            <button
                                key={status}
                                className={`filter-tab ${filter === status ? 'active' : ''}`}
                                onClick={() => setFilter(status)}
                            >
                                {status.charAt(0).toUpperCase() + status.slice(1)}
                            </button>
                        ))}
                    </div>
                </div>

                {loading ? (
                    <div className="loading">Loading...</div>
                ) : incidents.length > 0 ? (
                    <div className="incidents-table">
                        <div className="table-header">
                            <span>Service</span>
                            <span>Status</span>
                            <span>Severity</span>
                            <span>Detected</span>
                            <span>MTTD</span>
                            <span>MTTR</span>
                        </div>
                        {incidents.map(incident => (
                            <div key={incident.id} className="table-row">
                                <span className="service-cell">
                                    <strong>{incident.services?.name || 'Unknown'}</strong>
                                    <small>{incident.error_message?.slice(0, 50)}</small>
                                </span>
                                <span className={`status-badge ${incident.status}`}>
                                    {incident.status}
                                </span>
                                <span className={`severity-badge ${incident.severity}`}>
                                    {incident.severity}
                                </span>
                                <span className="date-cell">
                                    {new Date(incident.detected_at).toLocaleString()}
                                </span>
                                <span>{formatDuration(incident.mttd_seconds)}</span>
                                <span>{formatDuration(incident.mttr_seconds)}</span>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="empty-state-lg">
                        <div className="empty-icon">🎉</div>
                        <h3>No incidents</h3>
                        <p>All systems operational</p>
                    </div>
                )}
            </main>
        </div>
    )
}
