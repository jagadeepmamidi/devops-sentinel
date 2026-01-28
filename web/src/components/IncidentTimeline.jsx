import React, { useState, useEffect } from 'react';
import './IncidentTimeline.css';

const IncidentTimeline = ({ incidentId, events = [] }) => {
    const [timelineEvents, setTimelineEvents] = useState(events);
    const [loading, setLoading] = useState(!events.length);
    const [expandedEvent, setExpandedEvent] = useState(null);

    useEffect(() => {
        if (incidentId && !events.length) {
            fetchIncidentTimeline();
        }
    }, [incidentId]);

    const fetchIncidentTimeline = async () => {
        try {
            const response = await fetch(`/api/incidents/${incidentId}/timeline`);
            const data = await response.json();
            setTimelineEvents(data.events || []);
        } catch (error) {
            console.error('Failed to fetch timeline:', error);
        } finally {
            setLoading(false);
        }
    };

    const formatTime = (timestamp) => {
        if (!timestamp) return '';
        const date = new Date(timestamp);
        return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    };

    const formatDate = (timestamp) => {
        if (!timestamp) return '';
        const date = new Date(timestamp);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    };

    const getEventIcon = (eventType) => {
        const icons = {
            'detected': 'warning',
            'alert_sent': 'notifications',
            'acknowledged': 'check_circle',
            'investigating': 'search',
            'identified': 'lightbulb',
            'fix_applied': 'build',
            'monitoring': 'visibility',
            'resolved': 'done_all',
            'postmortem': 'description',
            'deployment': 'rocket_launch',
            'escalated': 'trending_up',
            'note': 'note'
        };
        return icons[eventType] || 'event';
    };

    const getEventColor = (eventType) => {
        const colors = {
            'detected': '#ef4444',
            'alert_sent': '#f97316',
            'acknowledged': '#eab308',
            'investigating': '#3b82f6',
            'identified': '#8b5cf6',
            'fix_applied': '#22c55e',
            'monitoring': '#06b6d4',
            'resolved': '#10b981',
            'postmortem': '#6366f1',
            'deployment': '#ec4899',
            'escalated': '#f43f5e',
            'note': '#64748b'
        };
        return colors[eventType] || '#64748b';
    };

    const calculateDuration = (event, index) => {
        if (index === 0) return null;

        const prevEvent = timelineEvents[index - 1];
        if (!prevEvent || !prevEvent.timestamp || !event.timestamp) return null;

        const diff = new Date(event.timestamp) - new Date(prevEvent.timestamp);
        const minutes = Math.floor(diff / 60000);

        if (minutes < 1) return 'Less than 1 min';
        if (minutes < 60) return `${minutes} min`;

        const hours = Math.floor(minutes / 60);
        const remainingMins = minutes % 60;
        return `${hours}h ${remainingMins}m`;
    };

    if (loading) {
        return (
            <div className="timeline-container">
                <div className="timeline-loading">Loading timeline...</div>
            </div>
        );
    }

    if (!timelineEvents.length) {
        return (
            <div className="timeline-container">
                <div className="timeline-empty">No timeline events available</div>
            </div>
        );
    }

    return (
        <div className="timeline-container">
            <h3 className="timeline-title">Incident Timeline</h3>

            <div className="timeline-summary">
                <div className="summary-item">
                    <span className="summary-label">Total Events</span>
                    <span className="summary-value">{timelineEvents.length}</span>
                </div>
                <div className="summary-item">
                    <span className="summary-label">Duration</span>
                    <span className="summary-value">
                        {timelineEvents.length > 1
                            ? calculateDuration(
                                timelineEvents[timelineEvents.length - 1],
                                timelineEvents.length - 1
                            )
                            : 'N/A'
                        }
                    </span>
                </div>
            </div>

            <div className="timeline">
                {timelineEvents.map((event, index) => (
                    <div
                        key={event.id || index}
                        className={`timeline-event ${expandedEvent === index ? 'expanded' : ''}`}
                        onClick={() => setExpandedEvent(expandedEvent === index ? null : index)}
                    >
                        <div className="event-connector">
                            <div
                                className="event-dot"
                                style={{ backgroundColor: getEventColor(event.type) }}
                            >
                                <span className="material-icons-outlined">
                                    {getEventIcon(event.type)}
                                </span>
                            </div>
                            {index < timelineEvents.length - 1 && (
                                <div className="event-line">
                                    {calculateDuration(timelineEvents[index + 1], index + 1) && (
                                        <span className="duration-badge">
                                            {calculateDuration(timelineEvents[index + 1], index + 1)}
                                        </span>
                                    )}
                                </div>
                            )}
                        </div>

                        <div className="event-content">
                            <div className="event-header">
                                <span
                                    className="event-type"
                                    style={{ color: getEventColor(event.type) }}
                                >
                                    {event.type?.replace('_', ' ').toUpperCase()}
                                </span>
                                <span className="event-time">
                                    {formatTime(event.timestamp)}
                                </span>
                            </div>

                            <div className="event-title">{event.title || event.message}</div>

                            {event.user && (
                                <div className="event-user">
                                    by {event.user.name || event.user.email}
                                </div>
                            )}

                            {expandedEvent === index && event.details && (
                                <div className="event-details">
                                    {typeof event.details === 'string'
                                        ? event.details
                                        : JSON.stringify(event.details, null, 2)
                                    }
                                </div>
                            )}

                            <div className="event-date">{formatDate(event.timestamp)}</div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default IncidentTimeline;
