"""
Machine Learning Training Module for Landslide & Flood Hazard Prediction
Target Corridor: Guwahati - Shillong (NH-6 / GS Road & Mountain Bypass)

Features:
1. Slope (Degrees) - CartoDEM (0 to 60°)
2. 24h Cumulative Rainfall (mm) - IMD / Open-Meteo (0 to 350 mm)
3. Soil Moisture (%) - IoT Sensor / In-situ (10% to 100%)
4. IMD Warning Level (0: Green, 1: Yellow, 2: Orange, 3: Red)

Output:
Segment Failure Probability (Risk Score: 0.0 to 1.0)
"""
import numpy as np
import os
import joblib
import json
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, roc_auc_score
from xgboost import XGBRegressor, XGBClassifier

def generate_synthetic_corridor_dataset(n_samples=5000, random_state=42):
    """
    Generates synthetic geotechnical and hydrometeorological dataset
    specifically calibrated to the East Khasi Hills / Ri-Bhoi / Kamrup terrain.
    """
    np.random.seed(random_state)
    
    # 1. Slope in degrees (NH6 plains: 2-8°, Hill sections Jorabat-Nongpoh: 15-35°, Mawlai/Barapani cliffs: 30-55°)
    slope = np.random.uniform(2.0, 58.0, size=n_samples)
    
    # 2. 24-hour Cumulative Rainfall in mm (Monsoon monsoon showers in Meghalaya / Cherrapunji-Shillong plateau)
    rain_24h = np.random.exponential(scale=45.0, size=n_samples)
    rain_24h = np.clip(rain_24h, 0.0, 320.0)
    
    # 3. Soil Moisture % (Influenced by recent rain + drainage)
    base_moisture = np.random.uniform(20.0, 45.0, size=n_samples)
    soil_moisture = np.clip(base_moisture + (rain_24h / 320.0) * 55.0 + np.random.normal(0, 4, size=n_samples), 10.0, 98.0)
    
    # 4. IMD Warning Level (0 to 3) derived from rain intensity
    imd_level = np.zeros(n_samples, dtype=int)
    imd_level[rain_24h > 30] = 1   # Yellow
    imd_level[rain_24h > 75] = 2   # Orange
    imd_level[rain_24h > 150] = 3  # Red
    # Add minor noise in official warnings
    flip_mask = np.random.rand(n_samples) < 0.08
    imd_level[flip_mask] = np.random.choice([0, 1, 2, 3], size=np.sum(flip_mask))
    
    # Compute Geotechnical Landslide & Flood Failure Probability (Ground Truth physics-informed formula)
    # Landslide factor = (Slope / 50)^1.8 * (Rain / 120)^1.4 * (Moisture / 80)^1.2
    # Flood factor (for low slope) = (Rain / 100)^1.6 * (1 / (Slope + 1)^0.5) * (Moisture / 70)
    
    landslide_component = (
        0.55 * np.power(np.clip(slope / 45.0, 0, 1.5), 1.7) *
        np.power(np.clip(rain_24h / 120.0, 0, 2.0), 1.5) *
        np.power(np.clip(soil_moisture / 75.0, 0, 1.3), 1.2)
    )
    
    flood_component = (
        0.45 * np.power(np.clip(rain_24h / 90.0, 0, 2.5), 1.6) *
        np.power(np.clip(soil_moisture / 80.0, 0, 1.3), 1.1) *
        (1.0 / np.sqrt(np.clip(slope, 1.0, 60.0)))
    )
    
    warning_boost = imd_level * 0.12
    
    raw_risk = landslide_component + flood_component + warning_boost + np.random.normal(0, 0.03, size=n_samples)
    # Sigmoidal squashing to strictly [0.0, 1.0]
    risk_score = 1.0 / (1.0 + np.exp(-4.5 * (raw_risk - 0.45)))
    risk_score = np.clip(risk_score, 0.0, 1.0)
    
    X = np.column_stack([slope, rain_24h, soil_moisture, imd_level])
    y = risk_score
    
    return X, y

def train_and_save_model(model_dir="backend/ml"):
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "landslide_flood_xgboost.joblib")
    meta_path = os.path.join(model_dir, "model_metadata.json")
    
    print("[*] Generating terrain-calibrated training dataset for Guwahati-Shillong corridor...")
    X, y = generate_synthetic_corridor_dataset(n_samples=6000)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("[*] Training XGBoost Risk Regressor...")
    model = XGBRegressor(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        objective="reg:squarederror",
        n_jobs=1,
        random_state=42
    )
    
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    y_pred = np.clip(y_pred, 0.0, 1.0)
    
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"[+] Model Training Complete!")
    print(f"    - Test MSE: {mse:.5f}")
    print(f"    - Test R2 Score: {r2:.4f}")
    
    # Save Model
    joblib.dump(model, model_path)
    print(f"[+] Saved model to {model_path}")
    
    metadata = {
        "features": ["slope_degrees", "cumulative_24h_rain_mm", "soil_moisture_pct", "imd_warning_level"],
        "mse": float(mse),
        "r2_score": float(r2),
        "target": "segment_failure_probability_0_to_1",
        "trained_date": "2026-09-16"
    }
    
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
        
    return model

if __name__ == "__main__":
    train_and_save_model()
