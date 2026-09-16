"""
Dynamic Dijkstra Disaster-Resilient Routing Engine
Calculates both standard shortest baseline path and AI-optimized safe bypass path
using real-time dynamic edge weighting:
Dynamic Weight = Distance * (1 + 10.0 * (Risk Score)^2)
Route Safety % = (1 - Average Segment Risk) * 100
"""
import networkx as nx
from typing import Dict, Any, List, Tuple
from backend.routing.graph_builder import corridor_graph, CORRIDOR_NODES
from backend.ml.risk_predictor import risk_predictor
from backend.ingestion.background_worker import ingestion_worker
from backend.ingestion.iot_sensor_stream import iot_manager
from backend.config import PENALTY_FACTOR

def evaluate_edge_dynamic_risk(
    u: str,
    v: str,
    edge_data: Dict[str, Any],
    weather_condition_override: str = None
) -> Dict[str, Any]:
    """
    Computes real-time dynamic risk for a road segment based on slope, rainfall, soil moisture, and alerts.
    """
    slope = edge_data.get("base_slope", 10.0)
    distance = edge_data.get("distance_km", 5.0)
    hazard_prone = edge_data.get("hazard_prone", "Low")
    
    # Check simulation condition
    sim_mode = weather_condition_override or iot_manager.simulation_mode
    
    # Default environmental readings
    rain_24h = 25.0
    soil_moisture = 35.0
    imd_level = 0
    
    if sim_mode == "RED" or sim_mode == "CLOUDBURST_JORABAT":
        if "jorabat" in [u, v]:
            rain_24h = 165.0
            soil_moisture = 88.0
            imd_level = 3
        elif "nongpoh" in [u, v] or "byrnihat" in [u, v]:
            rain_24h = 145.0
            soil_moisture = 82.0
            imd_level = 3
        elif "barapani_umiam" in [u, v]:
            rain_24h = 130.0
            soil_moisture = 78.0
            imd_level = 3
        else:
            rain_24h = 60.0
            soil_moisture = 55.0
            imd_level = 2
            
    elif sim_mode == "ORANGE":
        if "nongpoh" in [u, v] or "jorabat" in [u, v] or "barapani_umiam" in [u, v]:
            rain_24h = 85.0
            soil_moisture = 65.0
            imd_level = 2
        else:
            rain_24h = 35.0
            soil_moisture = 45.0
            imd_level = 1
            
    elif sim_mode == "LANDSLIDE_NONGPOH":
        if "nongpoh" in [u, v]:
            rain_24h = 180.0
            soil_moisture = 95.0
            imd_level = 3
        else:
            rain_24h = 20.0
            soil_moisture = 30.0
            imd_level = 0
            
    else:  # GREEN / NORMAL
        rain_24h = 8.0
        soil_moisture = 28.0
        imd_level = 0
        
    # ML Model Inference
    risk_info = risk_predictor.predict_segment_risk(
        slope_degrees=slope,
        rain_24h_mm=rain_24h,
        soil_moisture_pct=soil_moisture,
        imd_warning_level=imd_level
    )
    
    risk_score = risk_info["risk_score"]
    
    # Apply Dynamic Edge Weighting Formula:
    # Dynamic Weight = Distance * (1 + 10.0 * (Risk Score)^2)
    dynamic_weight = distance * (1.0 + PENALTY_FACTOR * (risk_score ** 2))
    
    return {
        "risk_score": risk_score,
        "dynamic_weight": round(dynamic_weight, 4),
        "hazard_type": risk_info["hazard_type"],
        "status": risk_info["status"],
        "inputs": risk_info["inputs"]
    }

def calculate_corridor_routes(
    origin: str,
    destination: str,
    weather_condition: str = None,
    emergency_severity: str = "CRITICAL"
) -> Dict[str, Any]:
    """
    Computes both the baseline shortest route and the AI disaster-resilient safe route.
    """
    if origin not in corridor_graph or destination not in corridor_graph:
        raise ValueError(f"Origin '{origin}' or Destination '{destination}' not in corridor network.")
        
    # Copy graph and apply updated dynamic weights and risk metrics
    G = corridor_graph.copy()
    
    evaluated_edges = {}
    high_risk_hazards_on_standard_path = []
    
    for u, v, data in G.edges(data=True):
        risk_res = evaluate_edge_dynamic_risk(u, v, data, weather_condition)
        G[u][v]["weight"] = risk_res["dynamic_weight"]
        G[u][v]["risk_score"] = risk_res["risk_score"]
        G[u][v]["hazard_type"] = risk_res["hazard_type"]
        G[u][v]["status"] = risk_res["status"]
        G[u][v]["dynamic_weight"] = risk_res["dynamic_weight"]
        
        edge_key = f"{u}--{v}"
        evaluated_edges[edge_key] = risk_res
        
    # 1. Compute Standard Shortest Baseline Path (Distance only)
    try:
        standard_path_nodes = nx.shortest_path(G, source=origin, target=destination, weight="distance_km")
    except nx.NetworkXNoPath:
        standard_path_nodes = []
        
    # 2. Compute AI Disaster-Resilient Path (Dynamic Dijkstra on Dynamic Weight)
    try:
        ai_safe_path_nodes = nx.shortest_path(G, source=origin, target=destination, weight="weight")
    except nx.NetworkXNoPath:
        ai_safe_path_nodes = []
        
    # Helper to construct detailed route payload
    def construct_route_payload(path_nodes: List[str], is_ai_optimized: bool):
        if not path_nodes or len(path_nodes) < 2:
            return None
            
        total_distance_km = 0.0
        total_dynamic_weight = 0.0
        segment_risks = []
        waypoints = []
        segments = []
        hazards_encountered = []
        
        for i in range(len(path_nodes)):
            node_id = path_nodes[i]
            node_data = CORRIDOR_NODES[node_id]
            waypoints.append({
                "node_id": node_id,
                "name": node_data["name"],
                "lat": node_data["lat"],
                "lng": node_data["lng"],
                "elevation_m": node_data["elevation_m"]
            })
            
            if i > 0:
                prev_node = path_nodes[i-1]
                edge_data = G[prev_node][node_id]
                dist = edge_data["distance_km"]
                risk = edge_data["risk_score"]
                dyn_w = edge_data["weight"]
                
                total_distance_km += dist
                total_dynamic_weight += dyn_w
                segment_risks.append(risk)
                
                if risk >= 0.40:
                    hazards_encountered.append({
                        "segment": f"{CORRIDOR_NODES[prev_node]['name']} -> {CORRIDOR_NODES[node_id]['name']}",
                        "hazard": edge_data["hazard_type"],
                        "risk_score": risk,
                        "road_name": edge_data["road_name"]
                    })
                    
                segments.append({
                    "from_node": prev_node,
                    "to_node": node_id,
                    "from_name": CORRIDOR_NODES[prev_node]["name"],
                    "to_name": CORRIDOR_NODES[node_id]["name"],
                    "road_name": edge_data["road_name"],
                    "road_type": edge_data["road_type"],
                    "distance_km": dist,
                    "risk_score": risk,
                    "hazard_type": edge_data["hazard_type"],
                    "status": edge_data["status"],
                    "dynamic_weight": dyn_w
                })
                
        avg_risk = sum(segment_risks) / len(segment_risks) if segment_risks else 0.0
        # Route Safety % = (1 - Average Segment Risk) * 100
        safety_pct = max(5.0, min(99.9, (1.0 - avg_risk) * 100.0))
        
        # Calculate ETA based on mountain road speeds and risk slowdown
        # Base speed 45 km/h, reduced by risk penalty
        speed_kmh = max(20.0, 48.0 * (1.0 - avg_risk * 0.4))
        travel_time_min = round((total_distance_km / speed_kmh) * 60)
        
        return {
            "path_nodes": path_nodes,
            "waypoints": waypoints,
            "segments": segments,
            "total_distance_km": round(total_distance_km, 2),
            "total_dynamic_weight": round(total_dynamic_weight, 2),
            "average_segment_risk": round(avg_risk, 4),
            "route_safety_pct": round(safety_pct, 1),
            "estimated_time_minutes": travel_time_min,
            "hazards_encountered": hazards_encountered
        }

    standard_route = construct_route_payload(standard_path_nodes, is_ai_optimized=False)
    ai_safe_route = construct_route_payload(ai_safe_path_nodes, is_ai_optimized=True)
    
    # Identify hazards avoided by AI safe route compared to standard route
    avoided_hazards = []
    if standard_route and ai_safe_route:
        std_hazards = standard_route.get("hazards_encountered", [])
        ai_hazards = ai_safe_route.get("hazards_encountered", [])
        ai_hazard_segs = {h["segment"] for h in ai_hazards}
        
        for h in std_hazards:
            if h["segment"] not in ai_hazard_segs:
                avoided_hazards.append({
                    "hazard_title": f"Avoided: {h['road_name']}",
                    "details": f"{h['hazard']} (Risk Index: {int(h['risk_score']*100)}%) on segment {h['segment']}",
                    "risk_score": h["risk_score"]
                })
                
    # If no hazards on standard path, mark clear
    if not avoided_hazards and standard_route and standard_route["route_safety_pct"] > 88.0:
        avoided_hazards.append({
            "hazard_title": "Corridor Clear",
            "details": "All primary highway segments within safe transit parameters.",
            "risk_score": 0.05
        })
        
    return {
        "origin": origin,
        "destination": destination,
        "origin_name": CORRIDOR_NODES[origin]["name"],
        "destination_name": CORRIDOR_NODES[destination]["name"],
        "condition": weather_condition or iot_manager.simulation_mode,
        "standard_route": standard_route,
        "ai_safe_route": ai_safe_route,
        "avoided_hazards": avoided_hazards,
        "safety_improvement_pct": round(ai_safe_route["route_safety_pct"] - standard_route["route_safety_pct"], 1) if (ai_safe_route and standard_route) else 0.0,
        "is_bypass_active": standard_path_nodes != ai_safe_path_nodes
    }
