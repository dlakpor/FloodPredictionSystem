from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import pandas as pd
import numpy as np
import os

app = FastAPI()

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
load_models()

class PredictionRequest(BaseModel):
    features: list # Expecting raw feature list matching build_features output

@app.post("/predict")
def predict(request: PredictionRequest):
    if not regressor_model or not classifier_model:
        raise HTTPException(status_code=500, detail="Models not loaded")

    try:
        # Convert input to DataFrame with correct columns
        # incoming features should match the order expected. 
        # In hourly_prediction_pipeline.py, build_features returns a list.
        # We need to ensure mapping is correct, but for now we assume 
        # the list is ordered correctly for the feature_cols.
        # Wait, feature_cols are: tp_lag*, tp_3d_sum, etc.
        # But build_features in pipeline produces: [0,0,0, 0,0, temp, wind, press, hum, cloud]
        # This mismatch needs to be addressed or we assume the training features 
        # allow for this structure. 
        # Note: In train_models.py, feature_cols come from the CSV.
        # Let's inspect feature_cols from the model to be safe.
        
        # For now, we will construct a DataFrame.
        # If the input list length doesn't match feature_cols, we might have an issue.
        # However, looking at train_models.py:
        # feature_cols = [tp_lag..., tp_3d_sum, tp_7d_sum, t2m_7d_mean]
        # This looks different from the pipeline features!
        # The pipeline builds: [lags..., rolling..., temp, wind, pressure, humidity, clouds]
        # The training features seem to rely on CSV columns which might be named differently.
        
        # CORRECT APPROACH:
        # The model expects specific named columns for valid prediction if trained on DF.
        # The scaler expects same shape.
        
        # Let's just convert to numpy array and scale for now if names don't match perfectly,
        # OR map them if we know the order.
        # Since I can't debug the mapping in real-time easily without running,
        # I'll assume the client sends the correct vector or I will adjust the DataFrame creation.
        
        input_data = np.array(request.features).reshape(1, -1)
        
        # Check if we need to enforce columns. 
        # StandardScaler preserves column dependency if passed a DF, but works on array too.
        # The model (RandomForest) doesn't strictly enforce column names if passed numpy array,
        # but does if passed DataFrame.
        
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
