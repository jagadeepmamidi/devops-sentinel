import React, { useState, useEffect, useRef } from 'react';
import './ServiceMap.css';

const ServiceMap = ({ teamId, services = [], dependencies = [] }) => {
    const [nodes, setNodes] = useState([]);
    const [edges, setEdges] = useState([]);
    const [selectedNode, setSelectedNode] = useState(null);
    const [loading, setLoading] = useState(true);
    const [viewMode, setViewMode] = useState('graph'); // 'graph' or 'list'
    const svgRef = useRef(null);
    const [dimensions, setDimensions] = useState({ width: 800, height: 500 });

    useEffect(() => {
        if (services.length && dependencies.length) {
            processData(services, dependencies);
            setLoading(false);
        } else if (teamId) {
            fetchServiceMap();
        }
    }, [teamId, services, dependencies]);

    useEffect(() => {
        const handleResize = () => {
            if (svgRef.current) {
                const container = svgRef.current.parentElement;
                setDimensions({
                    width: container.clientWidth,
                    height: Math.max(400, container.clientHeight)
                });
            }
        };

        handleResize();
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    const fetchServiceMap = async () => {
        try {
            const response = await fetch(`/api/teams/${teamId}/service-map`);
            const data = await response.json();
            processData(data.services, data.dependencies);
        } catch (error) {
            console.error('Failed to fetch service map:', error);
        } finally {
            setLoading(false);
        }
    };

    const processData = (servicesData, depsData) => {
        // Calculate positions using force-directed layout simulation
        const nodeMap = new Map();

        servicesData.forEach((service, index) => {
            const angle = (2 * Math.PI * index) / servicesData.length;
            const radius = Math.min(dimensions.width, dimensions.height) * 0.35;

            nodeMap.set(service.id, {
                id: service.id,
                name: service.name,
                status: service.status || 'unknown',
                criticality: service.criticality || 'standard',
                url: service.url,
                x: dimensions.width / 2 + radius * Math.cos(angle),
                y: dimensions.height / 2 + radius * Math.sin(angle),
                connections: 0
            });
        });

        // Count connections for node sizing
        depsData.forEach(dep => {
            const downstream = nodeMap.get(dep.downstream_service_id);
            const upstream = nodeMap.get(dep.upstream_service_id);
            if (downstream) downstream.connections++;
            if (upstream) upstream.connections++;
        });

        setNodes(Array.from(nodeMap.values()));
        setEdges(depsData.map(dep => ({
            source: dep.downstream_service_id,
            target: dep.upstream_service_id,
            type: dep.dependency_type || 'uses'
        })));
    };

    const getNodeRadius = (node) => {
        const base = 25;
        const connectionBonus = Math.min(node.connections * 3, 20);
        const criticalityBonus = node.criticality === 'critical' ? 10 : 0;
        return base + connectionBonus + criticalityBonus;
    };

    const getNodeColor = (status) => {
        const colors = {
            'healthy': '#10b981',
            'degraded': '#f59e0b',
            'unhealthy': '#ef4444',
            'unknown': '#6b7280'
        };
        return colors[status] || colors.unknown;
    };

    const getEdgePath = (edge) => {
        const source = nodes.find(n => n.id === edge.source);
        const target = nodes.find(n => n.id === edge.target);

        if (!source || !target) return '';

        // Curved path for better visibility
        const midX = (source.x + target.x) / 2;
        const midY = (source.y + target.y) / 2;
        const dx = target.x - source.x;
        const dy = target.y - source.y;
        const curveOffset = Math.sqrt(dx * dx + dy * dy) * 0.1;

        const controlX = midX - dy * curveOffset / Math.sqrt(dx * dx + dy * dy);
        const controlY = midY + dx * curveOffset / Math.sqrt(dx * dx + dy * dy);

        return `M ${source.x} ${source.y} Q ${controlX} ${controlY} ${target.x} ${target.y}`;
    };

    if (loading) {
        return (
            <div className="service-map-container">
                <div className="service-map-loading">Loading service map...</div>
            </div>
        );
    }

    if (!nodes.length) {
        return (
            <div className="service-map-container">
                <div className="service-map-empty">
                    <h3>No Services Found</h3>
                    <p>Add services to see your dependency map</p>
                </div>
            </div>
        );
    }

    return (
        <div className="service-map-container">
            <div className="service-map-header">
                <h3>Service Dependency Map</h3>
                <div className="view-toggle">
                    <button
                        className={viewMode === 'graph' ? 'active' : ''}
                        onClick={() => setViewMode('graph')}
                    >
                        Graph
                    </button>
                    <button
                        className={viewMode === 'list' ? 'active' : ''}
                        onClick={() => setViewMode('list')}
                    >
                        List
                    </button>
                </div>
            </div>

            <div className="service-map-legend">
                <div className="legend-item">
                    <span className="legend-dot" style={{ background: '#10b981' }}></span>
                    Healthy
                </div>
                <div className="legend-item">
                    <span className="legend-dot" style={{ background: '#f59e0b' }}></span>
                    Degraded
                </div>
                <div className="legend-item">
                    <span className="legend-dot" style={{ background: '#ef4444' }}></span>
                    Unhealthy
                </div>
                <div className="legend-item">
                    <span className="legend-dot" style={{ background: '#6b7280' }}></span>
                    Unknown
                </div>
            </div>

            {viewMode === 'graph' ? (
                <div className="service-map-graph" ref={svgRef}>
                    <svg width={dimensions.width} height={dimensions.height}>
                        <defs>
                            <marker
                                id="arrowhead"
                                markerWidth="10"
                                markerHeight="7"
                                refX="10"
                                refY="3.5"
                                orient="auto"
                            >
                                <polygon points="0 0, 10 3.5, 0 7" fill="#9ca3af" />
                            </marker>
                        </defs>

                        {/* Edges */}
                        <g className="edges">
                            {edges.map((edge, index) => (
                                <path
                                    key={index}
                                    d={getEdgePath(edge)}
                                    fill="none"
                                    stroke="#d1d5db"
                                    strokeWidth="2"
                                    markerEnd="url(#arrowhead)"
                                />
                            ))}
                        </g>

                        {/* Nodes */}
                        <g className="nodes">
                            {nodes.map(node => (
                                <g
                                    key={node.id}
                                    className={`node ${selectedNode === node.id ? 'selected' : ''}`}
                                    transform={`translate(${node.x}, ${node.y})`}
                                    onClick={() => setSelectedNode(selectedNode === node.id ? null : node.id)}
                                >
                                    <circle
                                        r={getNodeRadius(node)}
                                        fill={getNodeColor(node.status)}
                                        stroke={node.criticality === 'critical' ? '#000' : '#fff'}
                                        strokeWidth={node.criticality === 'critical' ? 3 : 2}
                                    />
                                    <text
                                        dy=".3em"
                                        textAnchor="middle"
                                        fill="#fff"
                                        fontSize="12"
                                        fontWeight="500"
                                    >
                                        {node.name.length > 10
                                            ? node.name.substring(0, 10) + '...'
                                            : node.name
                                        }
                                    </text>
                                </g>
                            ))}
                        </g>
                    </svg>
                </div>
            ) : (
                <div className="service-map-list">
                    {nodes.map(node => (
                        <div
                            key={node.id}
                            className={`service-list-item ${selectedNode === node.id ? 'selected' : ''}`}
                            onClick={() => setSelectedNode(selectedNode === node.id ? null : node.id)}
                        >
                            <div
                                className="status-indicator"
                                style={{ background: getNodeColor(node.status) }}
                            />
                            <div className="service-info">
                                <span className="service-name">{node.name}</span>
                                <span className="service-status">{node.status}</span>
                            </div>
                            <div className="connection-count">
                                {node.connections} connections
                            </div>
                            {node.criticality === 'critical' && (
                                <span className="critical-badge">CRITICAL</span>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {selectedNode && (
                <div className="service-details-panel">
                    {(() => {
                        const node = nodes.find(n => n.id === selectedNode);
                        if (!node) return null;

                        const incomingEdges = edges.filter(e => e.target === node.id);
                        const outgoingEdges = edges.filter(e => e.source === node.id);

                        return (
                            <>
                                <div className="panel-header">
                                    <h4>{node.name}</h4>
                                    <button onClick={() => setSelectedNode(null)}>Close</button>
                                </div>
                                <div className="panel-content">
                                    <div className="detail-row">
                                        <span className="label">Status</span>
                                        <span
                                            className="value status"
                                            style={{ color: getNodeColor(node.status) }}
                                        >
                                            {node.status}
                                        </span>
                                    </div>
                                    <div className="detail-row">
                                        <span className="label">Criticality</span>
                                        <span className="value">{node.criticality}</span>
                                    </div>
                                    <div className="detail-row">
                                        <span className="label">URL</span>
                                        <span className="value">{node.url || 'N/A'}</span>
                                    </div>

                                    {incomingEdges.length > 0 && (
                                        <div className="dependencies-section">
                                            <h5>Depends On ({incomingEdges.length})</h5>
                                            {incomingEdges.map((edge, i) => {
                                                const dep = nodes.find(n => n.id === edge.source);
                                                return dep ? (
                                                    <div key={i} className="dependency-item">
                                                        <span
                                                            className="dep-status"
                                                            style={{ background: getNodeColor(dep.status) }}
                                                        />
                                                        {dep.name}
                                                    </div>
                                                ) : null;
                                            })}
                                        </div>
                                    )}

                                    {outgoingEdges.length > 0 && (
                                        <div className="dependencies-section">
                                            <h5>Depended By ({outgoingEdges.length})</h5>
                                            {outgoingEdges.map((edge, i) => {
                                                const dep = nodes.find(n => n.id === edge.target);
                                                return dep ? (
                                                    <div key={i} className="dependency-item">
                                                        <span
                                                            className="dep-status"
                                                            style={{ background: getNodeColor(dep.status) }}
                                                        />
                                                        {dep.name}
                                                    </div>
                                                ) : null;
                                            })}
                                        </div>
                                    )}
                                </div>
                            </>
                        );
                    })()}
                </div>
            )}
        </div>
    );
};

export default ServiceMap;
