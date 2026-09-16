"""
Risk Predictor Module
Loads the trained XGBoost model and calculates road segment hazard failure risk.
"""
import os
import joblib
import numpy as np
from typing import Dict, Any, List

MODEL_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(MODEL_DIR, "landslide_flood_xgboost.joblib")

class HazardRiskPredictor:
    def __init__(self):
        self.model = None
        self._load_or_train_model()

    def _load_or_train_model(self):
        if not os.path.exists(MODEL_PATH):
            from backend.ml.train_model import train_and_save_model
            self.model = train_and_save_model(MODEL_DIR)
        else:
            try:
                self.model = joblib.load(MODEL_PATH)
            except Exception as e:
                print(f"[!] Error loading model: {e}. Retraining...")
                from backend.ml.train_model import train_and_save_model
                self.model = train_and_save_model(MODEL_DIR)

    def predict_segment_risk(
        self,
        slope_degrees: float,
        rain_24h_mm: float,
        soil_moisture_pct: float,
        imd_warning_level: int
    ) -> Dict[str, Any]:
        """
        Calculates failure risk probability for a single road segment.
        """
        features = np.array([[slope_degrees, rain_24h_mm, soil_moisture_pct, imd_warning_level]], dtype=np.float32)
        raw_pred = self.model.predict(features)[0]
        risk_score = float(np.clip(raw_pred, 0.0, 1.0))
        
        # Determine dominant hazard type
        if risk_score > 0.45:
            if slope_degrees >= 25.0:
                hazard_type = "High Landslide Threat"
            elif rain_24h_mm >= 80.0 and slope_degrees < 15.0:
                hazard_type = "Severe Flash Inundation / Flood"
            else:
                hazard_type = "Mudslide & Debris Flow Risk"
        elif risk_score > 0.25:
            hazard_type = "Moderate Weather Vulnerability"
        else:
            hazard_type = "Safe / Clear Transit"

        # Warning Category
        if risk_score >= 0.70:
            status = "CRITICAL_BLOCKED"
        elif risk_score >= 0.40:
            status = "WARNING_HIGH_RISK"
        elif risk_score >= 0.20:
            status = "ADVISORY_CAUTION"
        else:
            status = "NORMAL_CLEAR"

        return {
            "risk_score": round(risk_score, 4),
            "failure_probability": round(risk_score, 4),
            "hazard_type": hazard_type,
            "status": status,
            "inputs": {
                "slope_degrees": slope_degrees,
                "rain_24h_mm": rain_24h_mm,
                "soil_moisture_pct": soil_moisture_pct,
                "imd_warning_level": imd_warning_level
            }
        }

# Global singleton
risk_predictor = HazardRiskPredictor()
