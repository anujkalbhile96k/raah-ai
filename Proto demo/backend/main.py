"""
FastAPI Backend Application
AI Disaster Resilient Emergency Routing System (Guwahati - Shillong Corridor)
"""
import os
import json
import asyncio
from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.config import MONITORING_STATIONS, EMERGENCY_HOSPITALS
from backend.db.database import init_db
from backend.ml.risk_predictor import risk_predictor
from backend.ingestion.background_worker import ingestion_worker
from backend.ingestion.iot_sensor_stream import iot_manager
from backend.routing.graph_builder import CORRIDOR_NODES
from backend.routing.dynamic_dijkstra import calculate_corridor_routes

# Initialize FastAPI App
app = FastAPI(
    title="RAAH-AI Northeast Disaster Resilient Routing API",
    description="Emergency routing engine optimized for the Guwahati to Shillong Mountain Corridor",
    version="2.0.0"
)

# Enable CORS for open frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active WebSocket connections
connected_websockets = set()

# Models
class RouteRequest(BaseModel):
    origin: str
    destination: str
    weather_condition: Optional[str] = None
    emergency_severity: Optional[str] = "CRITICAL"

class SimulationRequest(BaseModel):
    condition: str # RED, ORANGE, GREEN, CLOUDBURST_JORABAT, LANDSLIDE_NONGPOH

@app.on_event("startup")
async def startup_event():
    print("[*] Initializing Database & Seeding Facilities...")
    init_db()
    print("[*] Starting Background Data Ingestion Worker...")
    ingestion_worker.start()

# API Endpoints
@app.get("/api/status")
def get_system_status():
    """Returns real-time system status and active telemetry."""
    return {
        "status": "ONLINE",
        "system": "RAAH-AI Disaster Resilient Routing Engine",
        "corridor": "Guwahati (Assam) -> Shillong (Meghalaya) NH-6",
        "ingestion": ingestion_worker.get_aggregated_status(),
        "total_nodes": len(CORRIDOR_NODES),
        "total_hospitals": len(EMERGENCY_HOSPITALS)
    }

@app.get("/api/corridor/nodes")
def get_corridor_nodes():
    """Returns all origin/destination waypoint nodes and hospital triage centers."""
    return {
        "nodes": CORRIDOR_NODES,
        "hospitals": EMERGENCY_HOSPITALS,
        "monitoring_stations": MONITORING_STATIONS
    }

@app.get("/api/weather/current")
def get_current_weather():
    """Returns live weather from Open-Meteo / IMD for the corridor."""
    return ingestion_worker.latest_weather_cache

@app.get("/api/sensors/stream")
def get_sensors_stream():
    """Returns live IoT sensor telemetry."""
    return iot_manager.get_latest_telemetry()

@app.post("/api/simulate/hazard")
async def set_simulated_hazard(req: SimulationRequest):
    """
    Triggers simulated extreme disaster conditions (e.g. Red Alert, Jorabat Inundation, Nongpoh Landslide).
    Broadcasts updates to all connected WebSockets.
    """
    result = iot_manager.set_simulation_condition(req.condition)
    # Broadcast to websocket clients
    payload = json.dumps({"type": "SENSOR_UPDATE", "data": result})
    for ws in list(connected_websockets):
        try:
            await ws.send_text(payload)
        except Exception:
            connected_websockets.remove(ws)
    return result

@app.post("/api/route/calculate")
def calculate_emergency_route(req: RouteRequest):
    """
    Computes both standard shortest path and AI dynamic Dijkstra disaster bypass path.
    """
    try:
        result = calculate_corridor_routes(
            origin=req.origin,
            destination=req.destination,
            weather_condition=req.weather_condition,
            emergency_severity=req.emergency_severity
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Routing failure: {str(e)}")

# Real-time WebSocket Endpoint
@app.websocket("/ws/sensors")
async def websocket_sensors_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.add(websocket)
    try:
        # Send immediate initial sensor state
        init_payload = {
            "type": "INITIAL_STATE",
            "data": {
                "simulation_mode": iot_manager.simulation_mode,
                "sensors": iot_manager.get_latest_telemetry()
            }
        }
        await websocket.send_text(json.dumps(init_payload))
        
        while True:
            # Keep-alive loop / receive any client messages
            data = await websocket.receive_text()
            # Handle potential ping/message
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        connected_websockets.remove(websocket)
    except Exception:
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)

# Static Files & Dashboard UI
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_index():
    # Check static/index.html or root index.html
    static_index = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(static_index):
        return FileResponse(static_index)
    root_index = os.path.join(os.path.dirname(__file__), "..", "index.html")
    if os.path.exists(root_index):
        return FileResponse(root_index)
    return {"message": "RAAH-AI Emergency Routing API Live."}
