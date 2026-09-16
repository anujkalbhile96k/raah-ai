"""
Database module for Disaster Resilient Routing System.
Provides connection management for PostGIS / SQLite and initial seeding.
"""
import sqlite3
import os
import json
from datetime import datetime
from backend.config import MONITORING_STATIONS, EMERGENCY_HOSPITALS

DB_FILE = os.path.join(os.path.dirname(__file__), "..", "disaster_routing.db")

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create tables if not exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sensor_telemetry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        station_id TEXT NOT NULL,
        station_name TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        hourly_rainfall_mm REAL DEFAULT 0.0,
        cumulative_24h_rain_mm REAL DEFAULT 0.0,
        soil_moisture_pct REAL DEFAULT 30.0,
        river_water_level_m REAL DEFAULT 1.2,
        imd_warning_level INTEGER DEFAULT 0,
        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS segment_risk_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        segment_code TEXT NOT NULL,
        ai_risk_score REAL NOT NULL,
        failure_probability REAL NOT NULL,
        dynamic_weight REAL NOT NULL,
        hazard_type TEXT DEFAULT 'Landslide/Flood',
        warning_status TEXT DEFAULT 'NORMAL',
        evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS emergency_facilities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        facility_id TEXT UNIQUE NOT NULL,
        facility_name TEXT NOT NULL,
        city TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        facility_type TEXT,
        icu_beds INTEGER DEFAULT 20,
        helipad INTEGER DEFAULT 0
    );
    """)

    # Seed emergency facilities
    for f_id, data in EMERGENCY_HOSPITALS.items():
        cursor.execute("""
        INSERT OR REPLACE INTO emergency_facilities 
        (facility_id, facility_name, city, latitude, longitude, facility_type, icu_beds, helipad)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f_id,
            data["name"],
            data["city"],
            data["lat"],
            data["lng"],
            data["type"],
            data.get("icu_beds", 20),
            1 if data.get("helipad", False) else 0
        ))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
