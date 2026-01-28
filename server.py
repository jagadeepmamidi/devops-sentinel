"""
DevOps Sentinel - API Server
=============================
FastAPI server with WebSocket support for real-time monitoring.
"""

import asyncio
from datetime import datetime
from typing import List, Optional
from uuid import UUID
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from config import settings
from models import ServiceConfig, Incident, IncidentStatus


# API Models
class ServiceCreate(BaseModel):
    name: str
    url: str
    check_interval: int = 10


class ServiceResponse(BaseModel):
    id: str
    name: str
    url: str
    check_interval: int
    is_active: bool


class IncidentResponse(BaseModel):
    id: str
    service_name: str
    status: str
    detected_at: str
    error_message: Optional[str]


# Initialize FastAPI
app = FastAPI(
    title="DevOps Sentinel",
    description="Autonomous SRE Agent System - API",
    version="1.0.0"
)


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


# Health endpoint
@app.get("/health")
async def health():
    """Health check for the Sentinel API itself."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# Services CRUD
@app.get("/api/services", response_model=List[ServiceResponse])
async def list_services():
    """List all monitored services."""
    from services.supabase_client import supabase_client
    
    if not supabase_client.is_connected:
        return []
    
    services = supabase_client.get_services()
    return [
        ServiceResponse(
            id=str(s.id),
            name=s.name,
            url=s.url,
            check_interval=s.check_interval,
            is_active=s.is_active
        )
        for s in services
    ]


@app.post("/api/services", response_model=ServiceResponse)
async def create_service(service: ServiceCreate):
    """Add a new service to monitor."""
    from services.supabase_client import supabase_client
    
    new_service = ServiceConfig(
        name=service.name,
        url=service.url,
        check_interval=service.check_interval
    )
    
    if supabase_client.is_connected:
        supabase_client.add_service(new_service)
    
    # Broadcast to WebSocket clients
    await manager.broadcast({
        "type": "service_added",
        "service": {
            "id": str(new_service.id),
            "name": new_service.name,
            "url": new_service.url
        }
    })
    
    return ServiceResponse(
        id=str(new_service.id),
        name=new_service.name,
        url=new_service.url,
        check_interval=new_service.check_interval,
        is_active=new_service.is_active
    )


@app.delete("/api/services/{service_id}")
async def delete_service(service_id: str):
    """Remove a service from monitoring."""
    from services.supabase_client import supabase_client
    
    try:
        uuid = UUID(service_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid service ID")
    
    if supabase_client.is_connected:
        supabase_client.delete_service(uuid)
    
    return {"status": "deleted"}


# Incidents
@app.get("/api/incidents", response_model=List[IncidentResponse])
async def list_incidents(limit: int = 50):
    """List recent incidents."""
    from services.supabase_client import supabase_client
    
    if not supabase_client.is_connected:
        return []
    
    incidents = supabase_client.get_incidents(limit=limit)
    return [
        IncidentResponse(
            id=str(inc.id),
            service_name=inc.service_name,
            status=inc.status.value,
            detected_at=inc.detected_at.isoformat(),
            error_message=inc.error_message
        )
        for inc in incidents
    ]


@app.get("/api/incidents/{incident_id}")
async def get_incident(incident_id: str):
    """Get incident details including postmortem."""
    from services.supabase_client import supabase_client
    
    try:
        uuid = UUID(incident_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid incident ID")
    
    if not supabase_client.is_connected:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    incident = supabase_client.get_incident(uuid)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    return {
        "id": str(incident.id),
        "service_name": incident.service_name,
        "service_url": incident.service_url,
        "status": incident.status.value,
        "detected_at": incident.detected_at.isoformat(),
        "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
        "error_code": incident.error_code,
        "error_message": incident.error_message,
        "postmortem": incident.action_plan
    }


# WebSocket for real-time updates
@app.websocket("/ws/monitor")
async def websocket_monitor(websocket: WebSocket):
    """WebSocket endpoint for real-time monitoring updates."""
    await manager.connect(websocket)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            
            # Handle commands from dashboard
            try:
                message = json.loads(data)
                if message.get("type") == "check_now":
                    url = message.get("url")
                    if url:
                        from tools import health_check_tool
                        result = health_check_tool._run(url)
                        await websocket.send_json({
                            "type": "health_check_result",
                            "url": url,
                            "result": result,
                            "timestamp": datetime.utcnow().isoformat()
                        })
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Dashboard
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the monitoring dashboard."""
    try:
        return FileResponse("dashboard/index.html")
    except Exception:
        return HTMLResponse(
            "<h1>DevOps Sentinel</h1>"
            "<p>Dashboard not found. Run from project root directory.</p>"
        )


# Mount static files for dashboard assets
try:
    app.mount("/static", StaticFiles(directory="dashboard"), name="static")
except Exception:
    pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.server_host, port=settings.server_port)
