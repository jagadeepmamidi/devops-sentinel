import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { supabase } from '../lib/supabase'
import Navbar from '../components/Navbar'
import './Dashboard.css'

export default function Dashboard() {
    const { user } = useAuth()
    const navigate = useNavigate()
    const [stats, setStats] = useState({
        projects: 0,
        services: 0,
        incidents: 0,
        avgMttd: '--'
    })
    const [recentIncidents, setRecentIncidents] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetchDashboardData()
    }, [user])

    const fetchDashboardData = async () => {
        if (!user) return

        try {
            // OPTIMIZED: Parallel fetching with Promise.all (async-parallel rule)
            const [projectsRes, servicesRes, incidentsRes, mttdRes] = await Promise.all([
                supabase.from('projects').select('*', { count: 'exact', head: true }),
                supabase.from('services').select('*', { count: 'exact', head: true }),
                supabase.from('incidents')
                    .select('*')
                    .neq('status', 'resolved')
                    .order('detected_at', { ascending: false })
                    .limit(5),
                supabase.from('incidents')
                    .select('mttd_seconds')
                    .not('mttd_seconds', 'is', null)
            ])

            const avgMttd = mttdRes.data?.length > 0
                ? (mttdRes.data.reduce((sum, i) => sum + i.mttd_seconds, 0) / mttdRes.data.length).toFixed(1)
                : '--'

            setStats({
                projects: projectsRes.count || 0,
                services: servicesRes.count || 0,
                incidents: incidentsRes.data?.length || 0,
                avgMttd: avgMttd + 's'
            })

            setRecentIncidents(incidentsRes.data || [])
        } catch (error) {
            console.error('Error fetching dashboard data:', error)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="dashboard-layout">
            <Navbar />
            <main className="dashboard-main">
                <div className="page-header">
                    <h1>Overview</h1>
                    <button className="btn btn-primary" onClick={() => navigate('/projects')}>
                        + New Project
                    </button>
                </div>

                <div className="stats-grid">
                    <div className="stat-card">
                        <div className="stat-value">{stats.projects}</div>
                        <div className="stat-label">Projects</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value">{stats.services}</div>
                        <div className="stat-label">Services</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value">{stats.incidents}</div>
                        <div className="stat-label">Open Incidents</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value">{stats.avgMttd}</div>
                        <div className="stat-label">Avg MTTD</div>
                    </div>
                </div>

                <div className="dashboard-grid">
                    <div className="card">
                        <div className="card-header">
                            <h3>Recent Incidents</h3>
                        </div>
                        <div className="card-body">
                            {recentIncidents.length > 0 ? (
                                <div className="incidents-list">
                                    {recentIncidents.map(incident => (
                                        <div key={incident.id} className="incident-item">
                                            <div className="incident-status" data-status={incident.status}></div>
                                            <div className="incident-info">
                                                <span className="incident-service">{incident.service_id}</span>
                                                <span className="incident-time">
                                                    {new Date(incident.detected_at).toLocaleString()}
                                                </span>
                                            </div>
                                            <span className={`incident-severity ${incident.severity}`}>
                                                {incident.severity}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="empty-state">
                                    <p>No active incidents</p>
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="card">
                        <div className="card-header">
                            <h3>Quick Actions</h3>
                        </div>
                        <div className="card-body">
                            <div className="quick-actions">
                                <button className="action-btn" onClick={() => navigate('/projects')}>
                                    <span className="action-icon">📁</span>
                                    Create Project
                                </button>
                                <button className="action-btn" onClick={() => navigate('/incidents')}>
                                    <span className="action-icon">🔍</span>
                                    View Incidents
                                </button>
                                <button className="action-btn" onClick={() => navigate('/postmortems')}>
                                    <span className="action-icon">📋</span>
                                    Postmortems
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    )
}
