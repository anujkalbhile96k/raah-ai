"""
Main Server Startup Script for RAAH-AI Northeast Disaster Resilient Routing System
Trains XGBoost model if needed, initializes DB, and launches Uvicorn server.
"""
import os
import sys
import uvicorn
from backend.ml.train_model import train_and_save_model
from backend.db.database import init_db

def bootstrap():
    print("==========================================================================")
    print("       RAAH-AI | DISASTER RESILIENT EMERGENCY ROUTING ENGINE              ")
    print("               Corridor: Guwahati (Assam) -> Shillong (Meghalaya)          ")
    print("==========================================================================")
    
    # 1. Initialize Database
    print("[1/3] Initializing Database & Corridor Nodes...")
    init_db()
    
    # 2. Check / Train XGBoost Risk Model
    model_path = os.path.join(os.path.dirname(__file__), "backend", "ml", "landslide_flood_xgboost.joblib")
    if not os.path.exists(model_path):
        print("[2/3] Training XGBoost Landslide & Flood Hazard Model...")
        train_and_save_model(os.path.join(os.path.dirname(__file__), "backend", "ml"))
    else:
        print("[2/3] XGBoost Risk Model verified and ready.")

    # 3. Start Server
    print("[3/3] Starting FastAPI Server on http://127.0.0.1:8000 ...")
    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    bootstrap()
