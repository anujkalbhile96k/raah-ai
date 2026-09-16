"""
Corridor Road Network Graph Builder
Constructs a high-fidelity geospatial road graph for the Guwahati to Shillong Emergency Corridor
including NH-6 (GS Road), mountain bypass detours, and emergency hospital nodes.
"""
import networkx as nx
from typing import Dict, Any, List
from backend.config import EMERGENCY_HOSPITALS

# Waypoint Coordinates database for key junctions and hospital nodes
CORRIDOR_NODES = {
    # Guwahati Hubs & Hospitals
    "gau_airport": {"name": "Guwahati Airport (GAU)", "lat": 26.1061, "lng": 91.5859, "elevation_m": 49},
    "excelcare": {"name": "Excelcare National Hospital", "lat": 26.1265, "lng": 91.6872, "elevation_m": 52},
    "paltan_bazar": {"name": "Guwahati Paltan Bazar / Station", "lat": 26.1804, "lng": 91.7539, "elevation_m": 55},
    "gmch": {"name": "GMCH Trauma Center (Bhangagarh)", "lat": 26.1558, "lng": 91.7772, "elevation_m": 62},
    "dispur": {"name": "Dispur Capital Complex", "lat": 26.1433, "lng": 91.7898, "elevation_m": 58},
    "downtown": {"name": "Down Town Hospital (Dispur)", "lat": 26.1360, "lng": 91.7925, "elevation_m": 60},
    "khanapara": {"name": "Khanapara Gateway Point", "lat": 26.1154, "lng": 91.8217, "elevation_m": 72},
    
    # NH-6 Choke Points & Towns
    "jorabat": {"name": "Jorabat Highway Junction", "lat": 26.0963, "lng": 91.8767, "elevation_m": 115},
    "byrnihat": {"name": "Byrnihat (Umtrew River Point)", "lat": 26.0489, "lng": 91.8845, "elevation_m": 185},
    "nongpoh": {"name": "Nongpoh Town (Ri-Bhoi HQ)", "lat": 25.9034, "lng": 91.8803, "elevation_m": 540},
    "nongpoh_civil": {"name": "Nongpoh Civil Hospital", "lat": 25.9015, "lng": 91.8790, "elevation_m": 545},
    "umsning": {"name": "Umsning Junction (NH6)", "lat": 25.7533, "lng": 91.9056, "elevation_m": 880},
    "barapani_umiam": {"name": "Barapani (Umiam Lake Bridge)", "lat": 25.6601, "lng": 91.9167, "elevation_m": 1040},
    "mawlai": {"name": "Mawlai Checkpoint", "lat": 25.6022, "lng": 91.8895, "elevation_m": 1420},
    
    # Alternate Mountain Bypass Nodes (Reinforced Disaster-Resilient Detours)
    "gorchuk_junction": {"name": "Gorchuk Highway Junction", "lat": 26.1189, "lng": 91.7102, "elevation_m": 65},
    "ranikhamar": {"name": "Ranikhamar Border Post", "lat": 25.9850, "lng": 91.7650, "elevation_m": 310},
    "mawlyndep": {"name": "Mawlyndep Ridge Route", "lat": 25.7011, "lng": 91.8210, "elevation_m": 920},
    "umroi_airport": {"name": "Umroi Airport (Shillong Regional)", "lat": 25.7032, "lng": 91.9785, "elevation_m": 995},
    "mawlyngkhung": {"name": "Mawlyngkhung High Plateau Bypass", "lat": 25.6420, "lng": 91.9640, "elevation_m": 1280},
    
    # Shillong Hubs & Hospitals
    "shillong_center": {"name": "Shillong Police Bazar / Central Hub", "lat": 25.5788, "lng": 91.8933, "elevation_m": 1520},
    "shillong_civil": {"name": "Shillong Civil Hospital", "lat": 25.5725, "lng": 91.8828, "elevation_m": 1495},
    "nazareth": {"name": "Nazareth Hospital (Laitumkhrah)", "lat": 25.5682, "lng": 91.8955, "elevation_m": 1530},
    "woodland": {"name": "Woodland Hospital (Dhankheti)", "lat": 25.5695, "lng": 91.8912, "elevation_m": 1515},
    "neigrihms": {"name": "NEIGRIHMS Apex Trauma Center", "lat": 25.5996, "lng": 91.9392, "elevation_m": 1460}
}

# Road segments definitions with geotechnical & routing baseline parameters
CORRIDOR_EDGES = [
    # --- Standard NH-6 / GS Road Corridor ---
    {
        "u": "paltan_bazar", "v": "gmch",
        "road_name": "GS Road Urban Corridor", "road_type": "urban",
        "distance_km": 3.8, "base_slope": 3.0, "lulc_rank": 0.12,
        "hazard_prone": "Low", "description": "Guwahati City Medical Arterial"
    },
    {
        "u": "gmch", "v": "dispur",
        "road_name": "GS Road Dispur Arterial", "road_type": "urban",
        "distance_km": 2.5, "base_slope": 2.5, "lulc_rank": 0.10,
        "hazard_prone": "Low", "description": "Dispur Link"
    },
    {
        "u": "dispur", "v": "downtown",
        "road_name": "Dispur Hospital Connector", "road_type": "urban",
        "distance_km": 1.2, "base_slope": 2.0, "lulc_rank": 0.10,
        "hazard_prone": "Low", "description": "Downtown Hospital Link"
    },
    {
        "u": "dispur", "v": "khanapara",
        "road_name": "GS Road - Khanapara Flyover", "road_type": "primary",
        "distance_km": 4.6, "base_slope": 4.0, "lulc_rank": 0.15,
        "hazard_prone": "Low", "description": "Khanapara Transit Section"
    },
    {
        "u": "khanapara", "v": "jorabat",
        "road_name": "NH-6 Khanapara-Jorabat Expressway", "road_type": "highway",
        "distance_km": 7.2, "base_slope": 14.5, "lulc_rank": 0.65,
        "hazard_prone": "Flood", "description": "Jorabat Inundation Choke Segment"
    },
    {
        "u": "jorabat", "v": "byrnihat",
        "road_name": "NH-6 Jorabat-Byrnihat Hill Pass", "road_type": "highway",
        "distance_km": 8.5, "base_slope": 18.0, "lulc_rank": 0.58,
        "hazard_prone": "Flood/Slide", "description": "Umtrew River Valley Pass"
    },
    {
        "u": "byrnihat", "v": "nongpoh",
        "road_name": "NH-6 Byrnihat-Nongpoh Mountain Section", "road_type": "highway",
        "distance_km": 24.5, "base_slope": 38.0, "lulc_rank": 0.88,
        "hazard_prone": "Landslide", "description": "Ri-Bhoi Critical Landslide Escarpment"
    },
    {
        "u": "nongpoh", "v": "nongpoh_civil",
        "road_name": "Nongpoh Hospital Link", "road_type": "urban",
        "distance_km": 0.8, "base_slope": 8.0, "lulc_rank": 0.20,
        "hazard_prone": "Low", "description": "Civil Hospital Access"
    },
    {
        "u": "nongpoh", "v": "umsning",
        "road_name": "NH-6 Nongpoh-Umsning Corridor", "road_type": "highway",
        "distance_km": 22.0, "base_slope": 24.0, "lulc_rank": 0.60,
        "hazard_prone": "Landslide", "description": "Umsning Hill Road"
    },
    {
        "u": "umsning", "v": "barapani_umiam",
        "road_name": "NH-6 Umsning-Barapani Lake Highway", "road_type": "highway",
        "distance_km": 14.5, "base_slope": 36.0, "lulc_rank": 0.82,
        "hazard_prone": "Landslide/Reservoir", "description": "Barapani Umiam Gorge Cut"
    },
    {
        "u": "barapani_umiam", "v": "mawlai",
        "road_name": "NH-6 Barapani-Mawlai Ascent", "road_type": "highway",
        "distance_km": 9.8, "base_slope": 28.0, "lulc_rank": 0.68,
        "hazard_prone": "Landslide", "description": "Shillong Approach Escarpment"
    },
    {
        "u": "mawlai", "v": "shillong_center",
        "road_name": "Mawlai - Police Bazar Arterial", "road_type": "urban",
        "distance_km": 4.5, "base_slope": 12.0, "lulc_rank": 0.25,
        "hazard_prone": "Low", "description": "Shillong City Arterial"
    },

    # --- Guwahati West / Airport Links ---
    {
        "u": "gau_airport", "v": "excelcare",
        "road_name": "NH-27 Airport-Boragaon Highway", "road_type": "highway",
        "distance_km": 12.0, "base_slope": 3.0, "lulc_rank": 0.10,
        "hazard_prone": "Low", "description": "Guwahati West Expressway"
    },
    {
        "u": "excelcare", "v": "gorchuk_junction",
        "road_name": "Boragaon-Gorchuk Arterial", "road_type": "primary",
        "distance_km": 3.5, "base_slope": 4.0, "lulc_rank": 0.12,
        "hazard_prone": "Low", "description": "Gorchuk Hub"
    },
    {
        "u": "gorchuk_junction", "v": "khanapara",
        "road_name": "Guwahati Southern Ring Bypass", "road_type": "highway",
        "distance_km": 14.2, "base_slope": 6.0, "lulc_rank": 0.18,
        "hazard_prone": "Low", "description": "Guwahati Southern Bypass"
    },

    # --- AI DISASTER RESILIENT BYPASS 1: West Mawlyndep Mountain Corridor ---
    # Bypasses the critical Jorabat flood bottleneck and Nongpoh landslide escarpment
    {
        "u": "gorchuk_junction", "v": "ranikhamar",
        "road_name": "Gorchuk-Ranikhamar Reinforced Link", "road_type": "bypass",
        "distance_km": 18.0, "base_slope": 12.0, "lulc_rank": 0.28,
        "hazard_prone": "Low", "description": "Stable Valley Bypass"
    },
    {
        "u": "ranikhamar", "v": "mawlyndep",
        "road_name": "Mawlyndep Mountain Bypass (Reinforced)", "road_type": "bypass",
        "distance_km": 32.0, "base_slope": 16.0, "lulc_rank": 0.32,
        "hazard_prone": "Low", "description": "Geotechnically Reinforced Bedrock Corridor"
    },
    {
        "u": "mawlyndep", "v": "mawlai",
        "road_name": "Mawlyndep-Mawlai Direct Ridge Cut", "road_type": "bypass",
        "distance_km": 14.8, "base_slope": 14.0, "lulc_rank": 0.30,
        "hazard_prone": "Low", "description": "Upper Ridge Access to Shillong"
    },

    # --- AI DISASTER RESILIENT BYPASS 2: Umroi / NEIGRIHMS East Plateau Bypass ---
    # Bypasses Barapani Umiam gorge and leads directly to Apex Trauma Center NEIGRIHMS
    {
        "u": "umsning", "v": "umroi_airport",
        "road_name": "Umsning-Umroi Airport Route", "road_type": "bypass",
        "distance_km": 11.2, "base_slope": 11.0, "lulc_rank": 0.26,
        "hazard_prone": "Low", "description": "Gentle Grade Airport Corridor"
    },
    {
        "u": "umroi_airport", "v": "mawlyngkhung",
        "road_name": "Umroi-Mawlyngkhung Plateau Link", "road_type": "bypass",
        "distance_km": 8.5, "base_slope": 13.0, "lulc_rank": 0.29,
        "hazard_prone": "Low", "description": "Stable Plateau Bypass"
    },
    {
        "u": "mawlyngkhung", "v": "neigrihms",
        "road_name": "Mawlyngkhung - NEIGRIHMS Emergency Access", "road_type": "primary",
        "distance_km": 6.8, "base_slope": 10.0, "lulc_rank": 0.22,
        "hazard_prone": "Low", "description": "Direct Apex Trauma Center Access"
    },

    # --- Shillong Hospital Distribution Network ---
    {
        "u": "shillong_center", "v": "shillong_civil",
        "road_name": "Civil Hospital Road", "road_type": "urban",
        "distance_km": 1.4, "base_slope": 8.0, "lulc_rank": 0.15,
        "hazard_prone": "Low", "description": "Shillong Civil Link"
    },
    {
        "u": "shillong_center", "v": "woodland",
        "road_name": "Dhankheti Hospital Link", "road_type": "urban",
        "distance_km": 1.8, "base_slope": 9.0, "lulc_rank": 0.15,
        "hazard_prone": "Low", "description": "Woodland Hospital Access"
    },
    {
        "u": "woodland", "v": "nazareth",
        "road_name": "Laitumkhrah Medical Link", "road_type": "urban",
        "distance_km": 1.1, "base_slope": 7.0, "lulc_rank": 0.15,
        "hazard_prone": "Low", "description": "Nazareth Hospital Link"
    },
    {
        "u": "shillong_center", "v": "neigrihms",
        "road_name": "New Shillong - NEIGRIHMS Arterial", "road_type": "primary",
        "distance_km": 8.2, "base_slope": 12.0, "lulc_rank": 0.24,
        "hazard_prone": "Low", "description": "Shillong to NEIGRIHMS Link"
    }
]

def build_corridor_graph() -> nx.Graph:
    """
    Builds the NetworkX undirected/bidirectional graph for the Guwahati-Shillong corridor.
    """
    G = nx.Graph()
    
    # Add nodes
    for node_id, data in CORRIDOR_NODES.items():
        G.add_node(
            node_id,
            name=data["name"],
            lat=data["lat"],
            lng=data["lng"],
            elevation_m=data["elevation_m"]
        )
        
    # Add edges
    for edge in CORRIDOR_EDGES:
        u = edge["u"]
        v = edge["v"]
        segment_code = f"SEG_{u.upper()}_{v.upper()}"
        G.add_edge(
            u, v,
            segment_code=segment_code,
            road_name=edge["road_name"],
            road_type=edge["road_type"],
            distance_km=edge["distance_km"],
            base_slope=edge["base_slope"],
            lulc_rank=edge["lulc_rank"],
            hazard_prone=edge["hazard_prone"],
            description=edge["description"]
        )
        
    return G

# Global Graph Singleton
corridor_graph = build_corridor_graph()
