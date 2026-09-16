-- PostGIS Schema for Northeast Disaster Resilient Emergency Routing Engine
-- Target Corridor: Guwahati (Assam) to Shillong (Meghalaya) via NH6

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- 1. Road Network Graph Table
CREATE TABLE IF NOT EXISTS road_segments (
    id SERIAL PRIMARY KEY,
    segment_code VARCHAR(50) UNIQUE NOT NULL,
    source_node VARCHAR(100) NOT NULL,
    target_node VARCHAR(100) NOT NULL,
    road_name VARCHAR(100) NOT NULL,
    road_type VARCHAR(50) DEFAULT 'primary', -- highway, bypass, urban, mountain_pass
    distance_km DOUBLE PRECISION NOT NULL,
    base_speed_kmh DOUBLE PRECISION NOT NULL DEFAULT 45.0,
    slope_degrees DOUBLE PRECISION NOT NULL DEFAULT 12.0, -- ISRO CartoDEM
    lulc_susceptibility DOUBLE PRECISION NOT NULL DEFAULT 0.35, -- ISRO Landslide ranking (0-1)
    elevation_start_m DOUBLE PRECISION NOT NULL DEFAULT 55.0,
    elevation_end_m DOUBLE PRECISION NOT NULL DEFAULT 1496.0,
    geom GEOMETRY(LineString, 4326),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_road_segments_geom ON road_segments USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_road_segments_nodes ON road_segments(source_node, target_node);

-- 2. Live Environmental & Sensor Readings Table
CREATE TABLE IF NOT EXISTS sensor_telemetry (
    id SERIAL PRIMARY KEY,
    station_id VARCHAR(50) NOT NULL,
    station_name VARCHAR(100) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    hourly_rainfall_mm DOUBLE PRECISION DEFAULT 0.0,
    cumulative_24h_rain_mm DOUBLE PRECISION DEFAULT 0.0,
    soil_moisture_pct DOUBLE PRECISION DEFAULT 30.0,
    river_water_level_m DOUBLE PRECISION DEFAULT 1.2,
    imd_warning_level INTEGER DEFAULT 0, -- 0: Green, 1: Yellow, 2: Orange, 3: Red
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sensor_telemetry_station ON sensor_telemetry(station_id, recorded_at DESC);

-- 3. Segment Risk Evaluations Cache
CREATE TABLE IF NOT EXISTS segment_risk_scores (
    id SERIAL PRIMARY KEY,
    segment_code VARCHAR(50) REFERENCES road_segments(segment_code),
    ai_risk_score DOUBLE PRECISION NOT NULL, -- 0.0 to 1.0
    failure_probability DOUBLE PRECISION NOT NULL,
    dynamic_weight DOUBLE PRECISION NOT NULL,
    hazard_type VARCHAR(50) DEFAULT 'Landslide/Flood',
    warning_status VARCHAR(20) DEFAULT 'NORMAL',
    evaluated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_segment_risk_code ON segment_risk_scores(segment_code, evaluated_at DESC);

-- 4. Emergency Facilities (Hospitals, Triage Centers, Relief Hubs)
CREATE TABLE IF NOT EXISTS emergency_facilities (
    id SERIAL PRIMARY KEY,
    facility_name VARCHAR(150) NOT NULL,
    facility_type VARCHAR(50) NOT NULL, -- Trauma Center, District Hospital, Relief Camp
    city VARCHAR(100) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    bed_capacity INTEGER DEFAULT 100,
    icu_available INTEGER DEFAULT 20,
    geom GEOMETRY(Point, 4326)
);

CREATE INDEX IF NOT EXISTS idx_facilities_geom ON emergency_facilities USING GIST(geom);
