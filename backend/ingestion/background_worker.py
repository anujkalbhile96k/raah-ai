"""
Background Ingestion Worker
Periodically orchestrates Open-Meteo weather polls, IoT streams, and Bhuvan data
to keep segment risk evaluations updated in real-time.
"""
import time
import threading
import datetime
from typing import Dict, Any
from backend.ingestion.imd_openmeteo import fetch_all_corridor_weather
from backend.ingestion.iot_sensor_stream import iot_manager
from backend.ingestion.isro_bhuvan import get_bhuvan_geotechnical_profile
from backend.config import INGESTION_INTERVAL_SECONDS

class BackgroundIngestionWorker:
    def __init__(self):
        self.running = False
        self.thread = None
        self.latest_weather_cache: Dict[str, Any] = {}
        self.last_sync_time: str = datetime.datetime.now().isoformat()
        
    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print("[*] Background Data Ingestion Worker started.")

    def stop(self):
        self.running = False

    def _run_loop(self):
        # Initial sync
        self._sync_once()
        while self.running:
            try:
                time.sleep(INGESTION_INTERVAL_SECONDS)
                self._sync_once()
            except Exception as e:
                print(f"[!] Error in ingestion worker loop: {e}")

    def _sync_once(self):
        try:
            self.latest_weather_cache = fetch_all_corridor_weather()
            self.last_sync_time = datetime.datetime.now().isoformat()
        except Exception as e:
            print(f"[!] Weather sync failed: {e}")

    def get_aggregated_status(self) -> Dict[str, Any]:
        return {
            "last_sync": self.last_sync_time,
            "weather": self.latest_weather_cache,
            "iot_sensors": iot_manager.get_latest_telemetry(),
            "simulation_mode": iot_manager.simulation_mode
        }

# Global worker singleton
ingestion_worker = BackgroundIngestionWorker()
