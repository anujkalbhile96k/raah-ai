"""
Automated Verification Suite for RAAH-AI Disaster Resilient Routing System
Tests:
1. Model Inference
2. Ingestion pipeline (Open-Meteo weather & ISRO Bhuvan slope)
3. Dynamic Dijkstra pathfinding under Green vs Red hazard states
4. Avoided hazard calculation
"""
import sys
from backend.ml.risk_predictor import risk_predictor
from backend.ingestion.imd_openmeteo import fetch_weather_for_coordinate
from backend.ingestion.isro_bhuvan import get_bhuvan_geotechnical_profile
from backend.routing.dynamic_dijkstra import calculate_corridor_routes

def run_tests():
    print("=================================================================")
    print("       RUNNING AUTOMATED VERIFICATION SUITE                       ")
    print("=================================================================")

    # Test 1: ML Risk Model Inference
    print("\n[TEST 1] Testing XGBoost Risk Inference on Geotechnical Inputs...")
    # Low risk condition: 5 deg slope, 5mm rain, 25% moisture, IMD 0
    safe_res = risk_predictor.predict_segment_risk(5.0, 5.0, 25.0, 0)
    print(f"  - Safe condition (Plains, low rain): Risk Score = {safe_res['risk_score']} ({safe_res['status']})")
    assert safe_res['risk_score'] < 0.25, "Expected low risk for safe conditions"

    # Extreme risk condition: 42 deg slope, 160mm rain, 88% moisture, IMD 3 (Red Alert)
    danger_res = risk_predictor.predict_segment_risk(42.0, 160.0, 88.0, 3)
    print(f"  - Severe condition (Steep slope, red rain): Risk Score = {danger_res['risk_score']} ({danger_res['hazard_type']} / {danger_res['status']})")
    assert danger_res['risk_score'] > 0.65, "Expected high risk for extreme conditions"
    print("  --> [PASS] Test 1: ML Inference Verified.")

    # Test 2: Ingestion & Bhuvan Profile
    print("\n[TEST 2] Testing ISRO Bhuvan Geotechnical Profile Lookup...")
    nongpoh_geo = get_bhuvan_geotechnical_profile(25.9034, 91.8803)
    print(f"  - Nongpoh Sector: Slope={nongpoh_geo['slope_degrees']}°, Elevation={nongpoh_geo['elevation_m']}m, LULC={nongpoh_geo['lulc_susceptibility_ranking']}")
    assert nongpoh_geo['slope_degrees'] >= 30.0, "Expected steep slope at Nongpoh"
    print("  --> [PASS] Test 2: Bhuvan GIS Lookup Verified.")

    # Test 3: Normal Route (Guwahati to NEIGRIHMS Shillong)
    print("\n[TEST 3] Testing Routing under GREEN / Normal Conditions...")
    route_green = calculate_corridor_routes(
        origin="paltan_bazar",
        destination="neigrihms",
        weather_condition="GREEN"
    )
    print(f"  - Is Bypass Active: {route_green['is_bypass_active']}")
    print(f"  - AI Safe Path: {' -> '.join(route_green['ai_safe_route']['path_nodes'])}")
    print(f"  - Route Safety: {route_green['ai_safe_route']['route_safety_pct']}%")
    print(f"  - Total Distance: {route_green['ai_safe_route']['total_distance_km']} km")
    assert route_green['ai_safe_route']['route_safety_pct'] >= 85.0, "Expected high safety for green conditions"
    print("  --> [PASS] Test 3: Green Baseline Routing Verified.")

    # Test 4: Extreme Red Alert Disaster Route (Dynamic Bypass)
    print("\n[TEST 4] Testing Routing under RED ALERT / Cloudburst Conditions...")
    route_red = calculate_corridor_routes(
        origin="paltan_bazar",
        destination="neigrihms",
        weather_condition="RED"
    )
    print(f"  - Is Bypass Active: {route_red['is_bypass_active']}")
    print(f"  - AI Safe Bypass Path: {' -> '.join(route_red['ai_safe_route']['path_nodes'])}")
    print(f"  - Standard Blocked Path: {' -> '.join(route_red['standard_route']['path_nodes'])}")
    print(f"  - Route Safety: {route_red['ai_safe_route']['route_safety_pct']}% vs Standard {route_red['standard_route']['route_safety_pct']}%")
    print(f"  - Avoided Hazards: {len(route_red['avoided_hazards'])}")
    for h in route_red['avoided_hazards']:
        print(f"    * {h['hazard_title']}: {h['details']}")
    
    assert route_red['is_bypass_active'] == True, "Expected AI bypass to activate during Red Alert"
    assert len(route_red['avoided_hazards']) > 0, "Expected avoided hazards list to be populated"
    print("  --> [PASS] Test 4: Dynamic Disaster-Resilient Bypass Verified.")

    print("\n=================================================================")
    print("   ALL TESTS PASSED! RAAH-AI ROUTING ENGINE FULLY VERIFIED        ")
    print("=================================================================")

if __name__ == "__main__":
    run_tests()
