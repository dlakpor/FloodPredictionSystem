from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import pandas as pd
import numpy as np
import os

app = FastAPI()

# render attaachment starts here
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # local Vite frontend
        "https://flood-prediction-system-eight.vercel.app"  # Vercel frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# render attachment ends here

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for models
regressor_model = None
classifier_model = None
scaler = None
feature_cols = None

def load_models():
    global regressor_model, classifier_model, scaler, feature_cols
    # Use path relative to this file (backend/api.py)
    # models are in ../models relative to backend/
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_dir = os.path.join(base_dir, "../models")
    
    try:
        reg_data = joblib.load(os.path.join(model_dir, "rf_regressor.joblib"))
        clf_data = joblib.load(os.path.join(model_dir, "rf_classifier.joblib"))
        
        regressor_model = reg_data["model"]
        classifier_model = clf_data["model"]
        scaler = reg_data["scaler"] # Using scaler from regressor (should be same)
        feature_cols = reg_data["features"]
        
        print("✅ Models loaded successfully")
    except Exception as e:
        print(f"⚠️ Error loading models: {e}")

# Load models on startup
from typing import List

class PredictionRequest(BaseModel):
    features: List[float]

    # Expecting raw feature list matching build_features output

@app.post("/predict")
def predict(request: PredictionRequest):
    if not regressor_model or not classifier_model:
        raise HTTPException(status_code=500, detail="Models not loaded")

    try:
             
        input_data = np.array(request.features).reshape(1, -1)
        input_scaled = scaler.transform(input_data)
        
        pred_rainfall = regressor_model.predict(input_scaled)[0]
        pred_proba = classifier_model.predict_proba(input_scaled)[0][1]
        
        flood_risk = "Low"
        if pred_proba > 0.7:
            flood_risk = "High"
        elif pred_proba > 0.4:
            flood_risk = "Moderate"

        return {
            "predicted_rainfall_mm": float(pred_rainfall),
            "flood_probability": float(pred_proba),
            "flood_risk": flood_risk
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/")
def root():
    return {"message": "Flood Prediction API is running"}
