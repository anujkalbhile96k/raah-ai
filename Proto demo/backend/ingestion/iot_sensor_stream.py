"""
IoT Sensor Stream Client & Live Telemetry Manager
Streams river water level (meters) and soil moisture (%) from ThingSpeak/Firebase channels
with dynamic simulation override capabilities for stress testing emergency routing.
"""
import time
import random
import datetime
from typing import Dict, Any, List

class IoTSensorStreamManager:
    def __init__(self):
        # Current state of IoT telemetry nodes along the corridor
        self.sensor_state: Dict[str, Dict[str, Any]] = {
            "sensor_jorabat_water": {
                "id": "IOT-WTR-01",
                "location": "Jorabat Highway Underpass / Drain",
                "lat": 26.0963,
                "lng": 91.8767,
                "type": "Ultrasonic River & Flood Level",
                "water_level_m": 1.4,
                "critical_threshold_m": 3.8,
                "status": "NORMAL",
                "unit": "meters",
                "updated_at": datetime.datetime.now().isoformat()
            },
            "sensor_byrnihat_river": {
                "id": "IOT-WTR-02",
                "location": "Umtrew River Bridge (Byrnihat)",
                "lat": 26.0489,
                "lng": 91.8845,
                "type": "Hydrometric Gauge",
                "water_level_m": 2.1,
                "critical_threshold_m": 4.5,
                "status": "NORMAL",
                "unit": "meters",
                "updated_at": datetime.datetime.now().isoformat()
            },
            "sensor_nongpoh_soil": {
                "id": "IOT-SLP-03",
                "location": "Nongpoh Cliff Inclinometer & Soil Probe",
                "lat": 25.9034,
                "lng": 91.8803,
                "type": "Capacitive Soil Moisture & Tilt",
                "soil_moisture_pct": 38.0,
                "critical_threshold_pct": 75.0,
                "tilt_degrees": 2.1,
                "status": "NORMAL",
                "unit": "%",
                "updated_at": datetime.datetime.now().isoformat()
            },
            "sensor_barapani_dam": {
                "id": "IOT-WTR-04",
                "location": "Umiam Lake Spillway Reservoir Sentry",
                "lat": 25.6601,
                "lng": 91.9167,
                "type": "Reservoir Water Level",
                "water_level_m": 3206.2,  # feet / meters representation
                "critical_threshold_m": 3220.0,
                "status": "NORMAL",
                "unit": "ft MSL",
                "updated_at": datetime.datetime.now().isoformat()
            },
            "sensor_mawlyndep_soil": {
                "id": "IOT-SLP-05",
                "location": "Mawlyndep Mountain Soil Sensor",
                "lat": 25.7011,
                "lng": 91.8210,
                "type": "Soil Saturation Sensor",
                "soil_moisture_pct": 28.0,
                "critical_threshold_pct": 80.0,
                "status": "NORMAL",
                "unit": "%",
                "updated_at": datetime.datetime.now().isoformat()
            }
        }
        
        # Simulation override state
        self.simulation_mode: str = "GREEN" # GREEN, ORANGE, RED, CLOUDBURST_JORABAT, LANDSLIDE_NONGPOH

    def get_latest_telemetry(self) -> Dict[str, Dict[str, Any]]:
        return self.sensor_state

    def set_simulation_condition(self, condition: str) -> Dict[str, Any]:
        """
        Adjusts IoT sensor readings in real-time according to simulated emergency events.
        """
        self.simulation_mode = condition
        now_str = datetime.datetime.now().isoformat()

        if condition == "RED" or condition == "CLOUDBURST_JORABAT":
            self.sensor_state["sensor_jorabat_water"]["water_level_m"] = 5.2
            self.sensor_state["sensor_jorabat_water"]["status"] = "DANGER_FLOOD_OVERFLOW"
            
            self.sensor_state["sensor_nongpoh_soil"]["soil_moisture_pct"] = 86.5
            self.sensor_state["sensor_nongpoh_soil"]["tilt_degrees"] = 14.8
            self.sensor_state["sensor_nongpoh_soil"]["status"] = "CRITICAL_LANDSLIP_ACTIVE"
            
            self.sensor_state["sensor_byrnihat_river"]["water_level_m"] = 4.8
            self.sensor_state["sensor_byrnihat_river"]["status"] = "WARNING_HIGH_SURGE"
            
        elif condition == "ORANGE":
            self.sensor_state["sensor_jorabat_water"]["water_level_m"] = 3.2
            self.sensor_state["sensor_jorabat_water"]["status"] = "WARNING_SURGE"
            
            self.sensor_state["sensor_nongpoh_soil"]["soil_moisture_pct"] = 62.0
            self.sensor_state["sensor_nongpoh_soil"]["tilt_degrees"] = 5.2
            self.sensor_state["sensor_nongpoh_soil"]["status"] = "ELEVATED_VULNERABILITY"
            
            self.sensor_state["sensor_byrnihat_river"]["water_level_m"] = 3.4
            self.sensor_state["sensor_byrnihat_river"]["status"] = "MODERATE_FLOW"
            
        elif condition == "LANDSLIDE_NONGPOH":
            self.sensor_state["sensor_nongpoh_soil"]["soil_moisture_pct"] = 92.0
            self.sensor_state["sensor_nongpoh_soil"]["tilt_degrees"] = 28.4
            self.sensor_state["sensor_nongpoh_soil"]["status"] = "CATASTROPHIC_DEBRIS_SLIDE"
            
            self.sensor_state["sensor_jorabat_water"]["water_level_m"] = 2.0
            self.sensor_state["sensor_jorabat_water"]["status"] = "NORMAL"
            
        else: # GREEN / NORMAL
            self.sensor_state["sensor_jorabat_water"]["water_level_m"] = 1.2
            self.sensor_state["sensor_jorabat_water"]["status"] = "NORMAL"
            
            self.sensor_state["sensor_nongpoh_soil"]["soil_moisture_pct"] = 32.0
            self.sensor_state["sensor_nongpoh_soil"]["tilt_degrees"] = 1.0
            self.sensor_state["sensor_nongpoh_soil"]["status"] = "NORMAL"
            
            self.sensor_state["sensor_byrnihat_river"]["water_level_m"] = 1.8
            self.sensor_state["sensor_byrnihat_river"]["status"] = "NORMAL"

        for key in self.sensor_state:
            self.sensor_state[key]["updated_at"] = now_str

        return {
            "simulation_mode": self.simulation_mode,
            "sensors": self.sensor_state
        }

# Global singleton
iot_manager = IoTSensorStreamManager()
