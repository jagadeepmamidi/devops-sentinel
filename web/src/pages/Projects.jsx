import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { supabase } from '../lib/supabase'
import Navbar from '../components/Navbar'
import './Projects.css'

export default function Projects() {
    const { user } = useAuth()
    const [projects, setProjects] = useState([])
    const [loading, setLoading] = useState(true)
    const [showModal, setShowModal] = useState(false)
    const [showServiceModal, setShowServiceModal] = useState(false)
    const [selectedProject, setSelectedProject] = useState(null)
    const [formData, setFormData] = useState({ name: '', description: '' })
    const [serviceData, setServiceData] = useState({ name: '', url: '', check_interval: 10 })

    useEffect(() => {
        fetchProjects()
    }, [user])

    const fetchProjects = async () => {
        if (!user) return

        console.log('Fetching projects for user:', user.id)

        // Fetch projects first
        const { data: projectsData, error: projectsError } = await supabase
            .from('projects')
            .select('*')
            .order('created_at', { ascending: false })

        if (projectsError) {
            console.error('Fetch projects error:', projectsError)
            alert(`Error fetching projects: ${projectsError.message}`)
            setLoading(false)
            return
        }

        // Fetch services separately
        const { data: servicesData } = await supabase
            .from('services')
            .select('*')

        // Attach services to their projects
        const projectsWithServices = (projectsData || []).map(project => ({
            ...project,
            services: (servicesData || []).filter(s => s.project_id === project.id)
        }))

        console.log('Projects with services:', projectsWithServices)
        setProjects(projectsWithServices)
        setLoading(false)
    }

    const createProject = async (e) => {
        e.preventDefault()

        const { data, error } = await supabase
            .from('projects')
            .insert({
                user_id: user.id,
                name: formData.name,
                description: formData.description
            })
            .select()

        if (error) {
            console.error('Create project error:', error)
            alert(`Failed to create project: ${error.message}\n\nMake sure you've created the 'projects' table in Supabase.`)
            return
        }

        setShowModal(false)
        setFormData({ name: '', description: '' })
        fetchProjects()
    }

    const addService = async (e) => {
        e.preventDefault()

        console.log('Adding service:', {
            user_id: user.id,
            project_id: selectedProject,
            name: serviceData.name,
            url: serviceData.url,
            check_interval: serviceData.check_interval
        })

        const { data, error } = await supabase
            .from('services')
            .insert({
                user_id: user.id,
                project_id: selectedProject,
                name: serviceData.name,
                url: serviceData.url,
                check_interval: serviceData.check_interval
            })
            .select()

        if (error) {
            console.error('Add service error:', error)
            alert(`Failed to add service: ${error.message}`)
            return
        }

        console.log('Service added:', data)
        setShowServiceModal(false)
        setServiceData({ name: '', url: '', check_interval: 10 })
        fetchProjects()
    }

    const deleteProject = async (projectId) => {
        if (!confirm('Delete this project and all its services?')) return

        await supabase.from('projects').delete().eq('id', projectId)
        fetchProjects()
    }

    return (
        <div className="dashboard-layout">
            <Navbar />
            <main className="dashboard-main">
                <div className="page-header">
                    <h1>Projects</h1>
                    <button className="btn btn-primary" onClick={() => setShowModal(true)}>
                        + New Project
                    </button>
                </div>

                {loading ? (
                    <div className="loading">Loading...</div>
                ) : projects.length > 0 ? (
                    <div className="projects-grid">
                        {projects.map(project => (
                            <div key={project.id} className="project-card">
                                <div className="project-header">
                                    <h3>{project.name}</h3>
                                    <button
                                        className="btn btn-ghost btn-sm"
                                        onClick={() => deleteProject(project.id)}
                                    >
                                        ×
                                    </button>
                                </div>
                                {project.description && (
                                    <p className="project-description">{project.description}</p>
                                )}
                                <div className="project-services">
                                    <h4>Services ({project.services?.length || 0})</h4>
                                    {project.services?.map(service => (
                                        <div key={service.id} className="service-item">
                                            <span className={`status-dot ${service.last_status}`}></span>
                                            <span className="service-name">{service.name}</span>
                                            <span className="service-url">{service.url}</span>
                                        </div>
                                    ))}
                                    <button
                                        className="btn btn-secondary btn-sm"
                                        onClick={() => {
                                            setSelectedProject(project.id)
                                            setShowServiceModal(true)
                                        }}
                                    >
                                        + Add Service
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="empty-state-lg">
                        <div className="empty-icon">📁</div>
                        <h3>No projects yet</h3>
                        <p>Create your first project to start monitoring services.</p>
                        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
                            Create Project
                        </button>
                    </div>
                )}

                {/* New Project Modal */}
                {showModal && (
                    <div className="modal-overlay" onClick={() => setShowModal(false)}>
                        <div className="modal" onClick={e => e.stopPropagation()}>
                            <h2>Create New Project</h2>
                            <form onSubmit={createProject}>
                                <div className="input-group">
                                    <label>Project Name</label>
                                    <input
                                        type="text"
                                        value={formData.name}
                                        onChange={e => setFormData({ ...formData, name: e.target.value })}
                                        placeholder="My API"
                                        required
                                    />
                                </div>
                                <div className="input-group">
                                    <label>Description (optional)</label>
                                    <textarea
                                        value={formData.description}
                                        onChange={e => setFormData({ ...formData, description: e.target.value })}
                                        placeholder="Production API monitoring"
                                    />
                                </div>
                                <div className="modal-actions">
                                    <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                                        Cancel
                                    </button>
                                    <button type="submit" className="btn btn-primary">
                                        Create Project
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}

                {/* Add Service Modal */}
                {showServiceModal && (
                    <div className="modal-overlay" onClick={() => setShowServiceModal(false)}>
                        <div className="modal" onClick={e => e.stopPropagation()}>
                            <h2>Add Service</h2>
                            <form onSubmit={addService}>
                                <div className="input-group">
                                    <label>Service Name</label>
                                    <input
                                        type="text"
                                        value={serviceData.name}
                                        onChange={e => setServiceData({ ...serviceData, name: e.target.value })}
                                        placeholder="Payment API"
                                        required
                                    />
                                </div>
                                <div className="input-group">
                                    <label>Health Check URL</label>
                                    <input
                                        type="url"
                                        value={serviceData.url}
                                        onChange={e => setServiceData({ ...serviceData, url: e.target.value })}
                                        placeholder="https://api.example.com/health"
                                        required
                                    />
                                </div>
                                <div className="input-group">
                                    <label>Check Interval (seconds)</label>
                                    <input
                                        type="number"
                                        value={serviceData.check_interval}
                                        onChange={e => setServiceData({ ...serviceData, check_interval: parseInt(e.target.value) })}
                                        min={5}
                                        max={300}
                                        required
                                    />
                                </div>
                                <div className="modal-actions">
                                    <button type="button" className="btn btn-secondary" onClick={() => setShowServiceModal(false)}>
                                        Cancel
                                    </button>
                                    <button type="submit" className="btn btn-primary">
                                        Add Service
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}
            </main>
        </div>
    )
}
