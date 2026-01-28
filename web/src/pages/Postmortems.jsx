import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { supabase } from '../lib/supabase'
import Navbar from '../components/Navbar'
import './Postmortems.css'

export default function Postmortems() {
    const { user } = useAuth()
    const [postmortems, setPostmortems] = useState([])
    const [loading, setLoading] = useState(true)
    const [selectedPostmortem, setSelectedPostmortem] = useState(null)

    useEffect(() => {
        fetchPostmortems()
    }, [user])

    const fetchPostmortems = async () => {
        if (!user) return

        const { data, error } = await supabase
            .from('incidents')
            .select(`
        *,
        services (name, url)
      `)
            .not('postmortem', 'is', null)
            .order('detected_at', { ascending: false })

        if (!error) setPostmortems(data || [])
        setLoading(false)
    }

    return (
        <div className="dashboard-layout">
            <Navbar />
            <main className="dashboard-main">
                <div className="page-header">
                    <h1>Postmortems</h1>
                </div>

                {loading ? (
                    <div className="loading">Loading...</div>
                ) : postmortems.length > 0 ? (
                    <div className="postmortems-grid">
                        {postmortems.map(pm => (
                            <div
                                key={pm.id}
                                className="postmortem-card"
                                onClick={() => setSelectedPostmortem(pm)}
                            >
                                <div className="pm-header">
                                    <span className={`severity-badge ${pm.severity}`}>{pm.severity}</span>
                                    <span className="pm-date">
                                        {new Date(pm.detected_at).toLocaleDateString()}
                                    </span>
                                </div>
                                <h3>{pm.services?.name || 'Unknown Service'}</h3>
                                <p className="pm-preview">
                                    {pm.postmortem?.slice(0, 150)}...
                                </p>
                                <div className="pm-footer">
                                    <span>MTTD: {pm.mttd_seconds?.toFixed(1)}s</span>
                                    <span>MTTR: {pm.mttr_seconds?.toFixed(1)}s</span>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="empty-state-lg">
                        <div className="empty-icon">📋</div>
                        <h3>No postmortems yet</h3>
                        <p>Postmortems are generated automatically when incidents are resolved.</p>
                    </div>
                )}

                {/* Postmortem Viewer Modal */}
                {selectedPostmortem && (
                    <div className="modal-overlay" onClick={() => setSelectedPostmortem(null)}>
                        <div className="modal modal-lg" onClick={e => e.stopPropagation()}>
                            <div className="modal-header">
                                <h2>Postmortem: {selectedPostmortem.services?.name}</h2>
                                <button
                                    className="btn btn-ghost"
                                    onClick={() => setSelectedPostmortem(null)}
                                >
                                    ×
                                </button>
                            </div>
                            <div className="postmortem-content">
                                <div className="pm-meta">
                                    <div className="meta-item">
                                        <span className="meta-label">Detected</span>
                                        <span>{new Date(selectedPostmortem.detected_at).toLocaleString()}</span>
                                    </div>
                                    <div className="meta-item">
                                        <span className="meta-label">Resolved</span>
                                        <span>
                                            {selectedPostmortem.resolved_at
                                                ? new Date(selectedPostmortem.resolved_at).toLocaleString()
                                                : 'Ongoing'}
                                        </span>
                                    </div>
                                    <div className="meta-item">
                                        <span className="meta-label">MTTD</span>
                                        <span>{selectedPostmortem.mttd_seconds?.toFixed(1)}s</span>
                                    </div>
                                    <div className="meta-item">
                                        <span className="meta-label">MTTR</span>
                                        <span>{selectedPostmortem.mttr_seconds?.toFixed(1)}s</span>
                                    </div>
                                </div>
                                <div className="pm-body">
                                    <pre>{selectedPostmortem.postmortem}</pre>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </main>
        </div>
    )
}
