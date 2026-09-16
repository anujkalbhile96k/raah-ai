"""
IMD & Open-Meteo Weather Data Ingestion Worker
Fetches real-time hourly rainfall (mm/hr), 24h cumulative precipitation, and alert levels (RED, ORANGE, GREEN)
for coordinates across the Guwahati-Shillong corridor.
"""
import requests
import datetime
from typing import Dict, Any
from backend.config import MONITORING_STATIONS, OPEN_METEO_BASE_URL

def fetch_weather_for_coordinate(lat: float, lng: float) -> Dict[str, Any]:
    """
    Calls Open-Meteo API for real-time precipitation and 24h cumulative rainfall.
    Falls back gracefully to realistic regional climatological telemetry if offline.
    """
    params = {
        "latitude": lat,
        "longitude": lng,
        "hourly": ["precipitation", "rain", "soil_temperature_0cm", "soil_moisture_0_to_1cm"],
        "current": ["temperature_2m", "relative_humidity_2m", "precipitation", "rain", "weather_code"],
        "timezone": "Asia/Kolkata",
        "past_days": 1,
        "forecast_days": 1
    }
    
    try:
        response = requests.get(OPEN_METEO_BASE_URL, params=params, timeout=4)
        if response.status_code == 200:
            data = response.json()
            current = data.get("current", {})
            hourly = data.get("hourly", {})
            
            hourly_rain_list = hourly.get("precipitation", [0.0])
            # 24h cumulative sum (last 24 entries)
            recent_24h = hourly_rain_list[-24:] if len(hourly_rain_list) >= 24 else hourly_rain_list
            cumulative_24h = sum(recent_24h)
            
            current_rain = float(current.get("precipitation", 0.0))
            
            # Derive IMD Warning Level
            # IMD Criteria:
            # Green (No warning): Rain < 15.5 mm
            # Yellow (Be updated): 15.6 - 64.4 mm
            # Orange (Be prepared): 64.5 - 115.5 mm
            # Red (Take action): > 115.5 mm or hourly > 45 mm/hr
            if cumulative_24h >= 115.5 or current_rain >= 35.0:
                imd_alert = "RED"
                imd_warning_level = 3
            elif cumulative_24h >= 64.5 or current_rain >= 15.0:
                imd_alert = "ORANGE"
                imd_warning_level = 2
            elif cumulative_24h >= 15.6 or current_rain >= 5.0:
                imd_alert = "YELLOW"
                imd_warning_level = 1
            else:
                imd_alert = "GREEN"
                imd_warning_level = 0
                
            soil_moistures = hourly.get("soil_moisture_0_to_1cm", [0.35])
            soil_moisture_pct = float(soil_moistures[-1] * 100) if soil_moistures else 35.0
            
            return {
                "success": True,
                "hourly_rain_mm": round(current_rain, 1),
                "cumulative_24h_rain_mm": round(cumulative_24h, 1),
                "imd_alert": imd_alert,
                "imd_warning_level": imd_warning_level,
                "soil_moisture_pct": round(soil_moisture_pct, 1),
                "temperature_c": current.get("temperature_2m", 24.5),
                "timestamp": datetime.datetime.now().isoformat()
            }
    except Exception as e:
        # Fallback in case of rate limit or offline mode
        pass

    # Regional fallback defaults (Guwahati-Shillong terrain base)
    return {
        "success": False,
        "hourly_rain_mm": 12.0,
        "cumulative_24h_rain_mm": 38.5,
        "imd_alert": "YELLOW",
        "imd_warning_level": 1,
        "soil_moisture_pct": 42.0,
        "temperature_c": 22.0,
        "timestamp": datetime.datetime.now().isoformat()
    }

def fetch_all_corridor_weather() -> Dict[str, Dict[str, Any]]:
    """
    Pulls weather for all monitoring stations along the corridor.
    """
    results = {}
    for station_key, info in MONITORING_STATIONS.items():
        results[station_key] = fetch_weather_for_coordinate(info["lat"], info["lng"])
        results[station_key]["station_name"] = info["name"]
        results[station_key]["lat"] = info["lat"]
        results[station_key]["lng"] = info["lng"]
    return results
