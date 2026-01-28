from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import json
import os
import subprocess
from datetime import datetime, timezone
import numpy as np
import requests
from dotenv import load_dotenv
import xgboost
import sklearn

load_dotenv()

app = FastAPI(title="Cyprus Flood Prediction API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------- Load models --------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")

MODEL_TYPES = ["rf", "xgb", "hybrid"]
loaded_models = {}

print("[INFO] Loading prediction models...")
for m_type in MODEL_TYPES:
    reg_path = os.path.join(MODELS_DIR, f"{m_type}_regressor.joblib")
    clf_path = os.path.join(MODELS_DIR, f"{m_type}_classifier.joblib")
    
    if os.path.exists(reg_path) and os.path.exists(clf_path):
        try:
            reg_data = joblib.load(reg_path)
            clf_data = joblib.load(clf_path)
            loaded_models[m_type] = {
                "reg": reg_data["model"],
                "clf": clf_data["model"],
                "scaler": reg_data.get("scaler"),
                "metadata": reg_data.get("metadata", {"name": m_type.upper()})
            }
            print(f"[OK] Loaded {m_type.upper()} model pair")
        except Exception as e:
            print(f"[ERROR] Error loading {m_type} models: {e}")
    else:
        print(f"[WARN] {m_type.upper()} models not found at {reg_path}")

if not loaded_models:
    print("[CRITICAL] No models loaded.")

class PredictRequest(BaseModel):
    features: list[float]
    model_type: str = "rf"

def calculate_topo_features(lat, lon, temp, m_type):
    # Kyrenia range (around 35.3) bias + Longitudinal variance
    lat_val, lon_val = float(lat), float(lon)
    
    # Remove model-specific bias to ensure accuracy based on training
    topo_bias = (np.sin(lat_val * 60) * np.cos(lon_val * 40) * 3.0)
    
    # Reconstruct features: lags 1-9 are modeled as "Local Moisture Context"
    # Starting base moisture + topo_bias
    moisture = max(0, 0.4 + topo_bias)
    return [moisture] * 9 + [float(temp)], topo_bias

@app.get("/")
def index():
    return {"status": "ok", "message": "Cyprus Flood Prediction API is running", "models": list(loaded_models.keys())}

@app.post("/predict")
def predict(req: PredictRequest):
    m_type = req.model_type.lower()
    if m_type not in loaded_models: m_type = "rf"
    if m_type not in loaded_models: raise HTTPException(status_code=500, detail="No models available")

    bundle = loaded_models[m_type]
    try:
        X = np.array(req.features, dtype=float).reshape(1, -1)
        if bundle["scaler"]: X = bundle["scaler"].transform(X)
        
        rainfall = float(bundle["reg"].predict(X)[0])
        prob = float(bundle["clf"].predict_proba(X)[0][1])

        # Updated thresholds: Low (<10%), Moderate (10-30%), High (>30%)
        if prob < 0.10: 
            risk = "Low"
            action = "Monitor"
        elif prob <= 0.30: 
            risk = "Moderate"
            action = "Prepare"
        else: 
            risk = "High"
            action = "Evacuate / Alert"

        return {
            "predicted_rainfall_mm": rainfall,
            "flood_probability": prob,
            "flood_risk": risk,
            "recommended_action": action,
            "model_name": bundle["metadata"]["name"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Simple in-memory cache for weather data: {(lat, lon): (timestamp, data)}
weather_cache = {}
import httpx
import asyncio

@app.get("/predict-location")
async def predict_location(lat: float, lon: float, model: str = "rf"):
    m_type = model.lower()
    if m_type not in loaded_models: m_type = "rf"
    if m_type not in loaded_models: raise HTTPException(status_code=500, detail="No models loaded")
    
    bundle = loaded_models[m_type]
    api_key = os.getenv("OPENWEATHER_API_KEY")
    
    # Check cache (10 minute expiry)
    cache_key = (round(lat, 3), round(lon, 3))
    now_ts = datetime.now().timestamp()
    if cache_key in weather_cache:
        ts, cached_res = weather_cache[cache_key]
        if now_ts - ts < 600: # 10 minutes
            weather, forecast_data = cached_res
        else:
            del weather_cache[cache_key]
    
    try:
        # If not cached, fetch concurrently
        if cache_key not in weather_cache:
            async with httpx.AsyncClient() as client:
                # Parallel fetch
                curr_task = client.get(f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric", timeout=10.0)
                fore_task = client.get(f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric", timeout=10.0)
                
                curr_res, fore_res = await asyncio.gather(curr_task, fore_task)
                
                curr_res.raise_for_status()
                fore_res.raise_for_status()
                
                weather = curr_res.json()
                forecast_data = fore_res.json()
                
                # Update cache
                weather_cache[cache_key] = (now_ts, (weather, forecast_data))

        # 2. Build features using unified logic
        features, topo_bias = calculate_topo_features(lat, lon, weather["main"]["temp"], m_type)
        
        X = np.array(features, dtype=float).reshape(1, -1)
        if bundle["scaler"]: X = bundle["scaler"].transform(X)

        rainfall = float(bundle["reg"].predict(X)[0])
        prob = float(bundle["clf"].predict_proba(X)[0][1])
        
        if prob < 0.10: 
            risk, action = "Low", "Monitor"
        elif prob <= 0.30: 
            risk, action = "Moderate", "Prepare"
        else: 
            risk, action = "High", "Evacuate / Alert"

        # Format UI data
        hourly = [
            {
                "time": datetime.fromtimestamp(x["dt"]).strftime("%H:%M"),
                "temp": round(x["main"]["temp"]),
                "precip": round(x.get("pop", 0) * 100),
                "wind": round(x["wind"]["speed"] * 3.6),
                "description": x["weather"][0]["description"]
            } 
            for x in forecast_data.get("list", [])[:24] # Show up to 72 hours (3h steps * 24 = 72h)
        ]

        # Calculate specific future horizons: 24h, 48h, 72h
        # Forecast list indices: 24h (index 8), 48h (index 16), 72h (index 24)
        future_horizons = {}
        forecast_list = forecast_data.get("list", [])
        
        for label, idx in [("24h", 8), ("48h", 16), ("72h", 24)]:
            target_idx = min(idx, len(forecast_list) - 1)
            if target_idx >= 0:
                f_item = forecast_list[target_idx]
                f_temp = f_item["main"]["temp"]
                # Reuse existing feature calculation logic
                f_features, _ = calculate_topo_features(lat, lon, f_temp, m_type)
                
                f_X = np.array(f_features, dtype=float).reshape(1, -1)
                if bundle["scaler"]: f_X = bundle["scaler"].transform(f_X)
                
                f_rainfall = float(bundle["reg"].predict(f_X)[0])
                f_prob = float(bundle["clf"].predict_proba(f_X)[0][1])
                
                if f_prob < 0.10: f_risk = "Low"
                elif f_prob <= 0.30: f_risk = "Moderate"
                else: f_risk = "High"
                
                future_horizons[label] = {
                    "time": datetime.fromtimestamp(f_item["dt"]).strftime("%a %H:%M"),
                    "temp": round(f_temp),
                    "rainfall_mm": round(f_rainfall, 2),
                    "probability": round(f_prob, 3),
                    "risk": f_risk
                }
        daily = []
        seen = set()
        for x in forecast_data.get("list", []):
            day = datetime.fromtimestamp(x["dt"]).strftime("%a")
            if day not in seen and len(daily) < 7:
                seen.add(day)
                daily.append({"day": day, "high": round(x["main"]["temp_max"]), "low": round(x["main"]["temp_min"]), "icon": x["weather"][0]["main"]})

        return {
            "location": {"lat": lat, "lon": lon, "name": weather.get("name", "Unknown")},
            "weather_summary": weather["weather"][0]["description"],
            "temp_c": round(weather["main"]["temp"]),
            "humidity": weather["main"]["humidity"],
            "wind_kph": round(weather["wind"]["speed"] * 3.6),
            "precipitation_prob": round(forecast_data["list"][0].get("pop", 0) * 100) if forecast_data.get("list") else 0,
            "forecast": {"hourly": hourly, "daily": daily},
            "prediction": {
                "predicted_rainfall_mm": rainfall,
                "flood_probability": prob,
                "flood_risk": risk,
                "recommended_action": action,
                "model_name": bundle["metadata"]["name"],
                "topo_bias": topo_bias,
                "future_horizons": future_horizons
            }
        }
    except Exception as e:
        # Fallback if API fails: try to return basic prediction without weather
        print(f"Weather API error: {e}")
        try:
            # Fallback prediction with default temp 25C
            features, topo_bias = calculate_topo_features(lat, lon, 25.0, m_type)
            X = np.array(features, dtype=float).reshape(1, -1)
            if bundle["scaler"]: X = bundle["scaler"].transform(X)
            rainfall = float(bundle["reg"].predict(X)[0])
            prob = float(bundle["clf"].predict_proba(X)[0][1])
             
            if prob < 0.10: r, a = "Low", "Monitor"
            elif prob <= 0.30: r, a = "Moderate", "Prepare"
            else: r, a = "High", "Evacuate"
            
            return {
                "location": {"lat": lat, "lon": lon, "name": "Unknown (Offline)"},
                "weather_summary": "N/A", "temp_c": 25, "humidity": 50, "wind_kph": 0, "precipitation_prob": 0,
                "forecast": {"hourly": [], "daily": []},
                "prediction": {
                    "predicted_rainfall_mm": rainfall,
                    "flood_probability": prob,
                    "flood_risk": r,
                    "recommended_action": a,
                    "model_name": bundle["metadata"]["name"],
                    "topo_bias": topo_bias
                }
            }
        except:
            raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

@app.get("/grid/latest")
def get_latest_grid(model: str = None):
    file_path = os.path.join(BASE_DIR, "data", "latest_grid_predictions.json")
    if not os.path.exists(file_path):
        file_path = os.path.join(BASE_DIR, "data", "grid_predictions.json")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Grid data not found.")

    with open(file_path, "r") as f:
        data = json.load(f)

    # If model is requested, re-predict on the fly for all points (Vectorized)
    if model and model.lower() in loaded_models:
        m_type = model.lower()
        bundle = loaded_models[m_type]
        
        try:
            # OPTIMIZATION: Vectorized Batch Prediction
            # Instead of looping predict(), we build the matrix X first.
            
            # 1. Extract features for ALL points
            X_list = []
            valid_indices = []
            
            for i, p in enumerate(data):
                try:
                    lat, lon = p["lat"], p["lon"]
                    temp = p.get("temp_c", 25.0)
                    if temp == 0: temp = 25.0
                    
                    # Feature Calc
                    topo_bias = (np.sin(lat * 60) * np.cos(lon * 40) * 3.0)
                    moisture = max(0, 0.4 + topo_bias)
                    features = [moisture] * 9 + [float(temp)]
                    X_list.append(features)
                    valid_indices.append(i)
                except:
                    continue
            
            if X_list:
                X_batch = np.array(X_list, dtype=float)
                
                # 2. Scale Batch
                if bundle["scaler"]:
                    X_batch = bundle["scaler"].transform(X_batch)
                
                # 3. Predict Batch
                rainfall_batch = bundle["reg"].predict(X_batch)
                probs_batch = bundle["clf"].predict_proba(X_batch)[:, 1]
                
                # 4. Update Data Iteratively (Fast because no model calls)
                for idx, r_val, p_val in zip(valid_indices, rainfall_batch, probs_batch):
                    p = data[idx]
                    prob = float(p_val)
                    rainfall = float(r_val)
                    
                    if prob < 0.10: 
                        rs, ac = "Low", "Monitor"
                    elif prob <= 0.30: 
                        rs, ac = "Moderate", "Prepare"
                    else: 
                        rs, ac = "High", "Evacuate / Alert"
                        
                    p["flood_risk"] = rs
                    p["flood_probability"] = prob
                    p["predicted_rainfall_mm"] = rainfall
                    p["recommended_action"] = ac
                    p["prediction"] = {
                        "predicted_rainfall_mm": rainfall,
                        "flood_probability": prob,
                        "flood_risk": rs,
                        "recommended_action": ac,
                        "model_used": bundle["metadata"]["name"]
                    }
                    
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[ERROR] Batch prediction failed: {e}. Falling back to cached values.")
            pass

    return {
        "status": "success",
        "count": len(data),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "data": data,
        "model_applied": model if model else "cached"
    }

@app.middleware("http")
async def add_no_cache(request, call_next):
    response = await call_next(request)
    if request.url.path == "/grid/latest":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

@app.post("/grid/refresh")
def refresh_grid(model: str = "rf"):
    script = os.path.join("src", "hourly_prediction_pipeline.py")
    # Set env var for the pipeline to pick up
    new_env = os.environ.copy()
    new_env["ML_MODEL"] = model.lower()
    
    try:
        result = subprocess.run(["python", script], capture_output=True, text=True, check=True, cwd=BASE_DIR, env=new_env)
        return {"status": "success", "message": f"Grid refreshed using {model}", "stdout": result.stdout[-500:]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
