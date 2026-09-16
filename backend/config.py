"""
Configuration module for Disaster Resilient Emergency Routing Engine.
Guwahati to Shillong Corridor (NH-6 / GS Road & Mountain Detours).
"""
import os

# Corridor Center & Default Coordinates
CORRIDOR_CENTER = {"lat": 25.8600, "lng": 91.8100}

# Target Corridor Monitoring Stations & Geo Coordinates
MONITORING_STATIONS = {
    "guwahati": {
        "name": "Guwahati Met Station (Assam)",
        "lat": 26.1445,
        "lng": 91.7362,
        "type": "Met & River Gauge (Brahmaputra/Bharalu)"
    },
    "jorabat": {
        "name": "Jorabat Flash Flood Sentry (Assam-Meghalaya Border)",
        "lat": 26.0963,
        "lng": 91.8767,
        "type": "Flood Gauge & Drain Sentry"
    },
    "byrnihat": {
        "name": "Byrnihat Industrial Corridor (Meghalaya)",
        "lat": 26.0489,
        "lng": 91.8845,
        "type": "Rain & River Sensor (Umtrew River)"
    },
    "nongpoh": {
        "name": "Nongpoh Landslide Monitoring Point (Ri-Bhoi)",
        "lat": 25.9034,
        "lng": 91.8803,
        "type": "Slope Inclinometer & Soil Moisture"
    },
    "umsning": {
        "name": "Umsning Bypass Weather Post",
        "lat": 25.7533,
        "lng": 91.9056,
        "type": "Rainfall & Road Surface Sensor"
    },
    "umiam": {
        "name": "Umiam Dam Catchment Sensor (Barapani)",
        "lat": 25.6601,
        "lng": 91.9167,
        "type": "Reservoir Level & Inundation Sentry"
    },
    "mawlyndep": {
        "name": "Mawlyndep Mountain Detour Station",
        "lat": 25.7011,
        "lng": 91.8210,
        "type": "Soil Stability Sensor"
    },
    "shillong": {
        "name": "Shillong Met & Highland Observatory",
        "lat": 25.5788,
        "lng": 91.8933,
        "type": "Highland AWS & Soil Sensor"
    }
}

# Major Emergency Hospitals & Triage Centers
EMERGENCY_HOSPITALS = {
    "gmch": {
        "name": "Guwahati Medical College & Hospital (GMCH)",
        "city": "Guwahati",
        "lat": 26.1558,
        "lng": 91.7772,
        "type": "Level 1 Trauma Center",
        "icu_beds": 85,
        "helipad": True
    },
    "downtown": {
        "name": "Down Town Hospital (Dispur)",
        "city": "Guwahati",
        "lat": 26.1360,
        "lng": 91.7925,
        "type": "Super Specialty Trauma Hub",
        "icu_beds": 45,
        "helipad": False
    },
    "excelcare": {
        "name": "Excelcare National Hospital (Boragaon)",
        "city": "Guwahati",
        "lat": 26.1265,
        "lng": 91.6872,
        "type": "Emergency Tertiary Care",
        "icu_beds": 35,
        "helipad": False
    },
    "nongpoh_civil": {
        "name": "Nongpoh Civil Hospital (Ri-Bhoi District)",
        "city": "Nongpoh",
        "lat": 25.9015,
        "lng": 91.8790,
        "type": "Highway Emergency Stabilization Center",
        "icu_beds": 12,
        "helipad": False
    },
    "neigrihms": {
        "name": "NEIGRIHMS Super Specialty Hospital",
        "city": "Shillong",
        "lat": 25.5996,
        "lng": 91.9392,
        "type": "Apex Regional Referral & Trauma Center",
        "icu_beds": 70,
        "helipad": True
    },
    "shillong_civil": {
        "name": "Shillong Civil Hospital",
        "city": "Shillong",
        "lat": 25.5725,
        "lng": 91.8828,
        "type": "State District Hospital",
        "icu_beds": 30,
        "helipad": False
    },
    "nazareth": {
        "name": "Nazareth Hospital (Laitumkhrah)",
        "city": "Shillong",
        "lat": 25.5682,
        "lng": 91.8955,
        "type": "Multi-Specialty Emergency Care",
        "icu_beds": 25,
        "helipad": False
    },
    "woodland": {
        "name": "Woodland Hospital (Dhankheti)",
        "city": "Shillong",
        "lat": 25.5695,
        "lng": 91.8912,
        "type": "Emergency Critical Care",
        "icu_beds": 20,
        "helipad": False
    }
}

# Penalty multiplier for dynamic edge weighting: Dynamic Weight = Distance * (1 + PENALTY_FACTOR * (Risk Score)^2)
PENALTY_FACTOR = 10.0

# Open-Meteo Weather API Endpoint
OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"

# Ingestion Polling Interval in seconds
INGESTION_INTERVAL_SECONDS = 60

# Database Connection (Postgres/PostGIS connection string or fallback SQLite)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./disaster_routing.db")
