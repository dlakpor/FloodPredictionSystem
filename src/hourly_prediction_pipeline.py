import requests
import json
import csv
import os
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_URL = "http://127.0.0.1:8000/predict"
DEFAULT_MODEL = os.getenv("ML_MODEL", "rf") # Default to RF if not specified
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

GRID_FILE = "data/cyprus_grid_points.json"
OUTPUT_FILE_CSV = "data/hourly_predictions.csv"
OUTPUT_FILE_JSON = "data/latest_grid_predictions.json"


# Polygon defining the approximate border of North Cyprus (High Fidelity v4)
# Matches the frontend implementation for consistent filtering
NORTH_CYPRUS_POLYGON = [
    # West Coast & Morphou Bay
    (35.08, 32.75), # Lefke Inland
    (35.15, 32.85), # Morphou West Coast
    (35.22, 32.94), # Morphou Bay Deep
    (35.32, 32.93), # Morphou Bay North / Kormakitis West

    # Cape Kormakitis (Circle 1 Fix: Shaved Tip)
    (35.40, 32.95), # Shaved Tip South-West a bit
    (35.36, 33.10), # Kormakitis East

    # Kyrenia Coast
    (35.34, 33.25), # Lapta/Alsancak
    (35.33, 33.35), # Kyrenia Harbor
    (35.34, 33.55), # Catalkoy / Esentepe West

    # Esentepe & Kantara
    (35.38, 33.75), # Esentepe Coast
    (35.42, 33.95), # Tatlisu
    (35.47, 34.08), # Kaplica / Kantara North

    # Karpaz Peninsula - North Side
    (35.54, 34.22), # Yeni Erenkoy
    (35.60, 34.38), # Dipkarpaz North
    (35.67, 34.54), # Zafer Burnu (Tip North) - Retracted
    (35.69, 34.58), # The Absolute Tip - Retracted West (Circle 3 Fix)

    # Karpaz Peninsula - South Side
    (35.65, 34.58), # Tip South - Retracted West
    (35.58, 34.50), # Dipkarpaz South - Shaved
    (35.52, 34.35), # Kaleburnu
    (35.45, 34.20), # Balalan Coast
    (35.38, 34.10), # Bogaz North

    # Famagusta Bay (Circle 2 Fix: Deep Cut Inland)
    (35.28, 33.97), # Iskele / Long Beach - Pushed West
    (35.20, 33.92), # Glapsides - Pushed West
    (35.12, 33.94), # Famagusta Port - Tightened

    # The Green Line (Border)
    (35.09, 33.92), # Varosha South limit
    (35.10, 33.70), # Mesaoria Border East
    (35.12, 33.50), # Nicosia North Border
    (35.16, 33.35), # Nicosia West Buffer
    (35.14, 33.15), # Morphou Plain Border
    (35.10, 32.90)  # Back to Lefke area
]

def is_point_in_polygon(lat, lon, polygon):
    """
    Ray-casting algorithm for point in polygon.
    """
    num_vertices = len(polygon)
    x, y = lat, lon
    inside = False
 
    p1x, p1y = polygon[0]
    for i in range(num_vertices + 1):
        p2x, p2y = polygon[i % num_vertices]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
 
    return inside


def fetch_weather(lat, lon):
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
    )
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json()


def build_features(weather):
    # Match the 10 features expected by the model
    # [tp_lag1..7, tp_3d_sum, tp_7d_sum, t2m_7d_mean]
    # We use 0 as default for lags since we don't have historical data here
    temp = weather["main"]["temp"] if "main" in weather else 0
    return [0, 0, 0, 0, 0, 0, 0, 0, 0, temp]


def ensure_csv():
    if not os.path.exists(OUTPUT_FILE_CSV):
        with open(OUTPUT_FILE_CSV, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp", "lat", "lon",
                "predicted_rainfall_mm",
                "flood_probability",
                "flood_risk"
            ])


def run_pipeline():
    if not os.path.exists(GRID_FILE):
        print(f"❌ Grid file not found: {GRID_FILE}")
        return

    with open(GRID_FILE, "r") as f:
        grid = json.load(f)

    ensure_csv()
    timestamp = datetime.utcnow().isoformat()
    
    predictions = []

    print(f"Starting pipeline. Total grid points: {len(grid)}")
    
    processed_count = 0
    skipped_count = 0

    for point in grid:
        lat, lon = point["lat"], point["lon"]

        # Filter Ocean/River Points by Polygon
        if not is_point_in_polygon(lat, lon, NORTH_CYPRUS_POLYGON):
            skipped_count += 1
            continue

        try:
            weather = fetch_weather(lat, lon)
            time.sleep(0.2) # Avoid rate limit
            loc_name = weather.get("name", "").lower()
            
            # Simple keyword filter for water bodies
            if any(w in loc_name for w in ["sea", "ocean", "mediterranean", "bay", "gulf"]):
                skipped_count += 1
                continue
            features = build_features(weather)

            response = requests.post(
                API_URL,
                json={"features": features, "model_type": DEFAULT_MODEL},
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            
            # Add to CSV list
            with open(OUTPUT_FILE_CSV, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp,
                    lat,
                    lon,
                    result["predicted_rainfall_mm"],
                    result["flood_probability"],
                    result["flood_risk"]
                ])
            
            # Add to JSON list
            predictions.append({
                "lat": lat,
                "lon": lon,
                "location_name": weather.get("name", f"Loc ({lat:.2f}, {lon:.2f})"), 
                "weather_summary": weather["weather"][0]["description"] if "weather" in weather else "N/A",
                "temp_c": weather["main"]["temp"] if "main" in weather else 0,
                "prediction": result, 
                "flood_risk": result["flood_risk"], 
                "flood_probability": result["flood_probability"],
                "predicted_rainfall_mm": result["predicted_rainfall_mm"],
                "timestamp": timestamp
            })
            processed_count += 1
            # Rate limiting or print progress every 10
            if processed_count % 10 == 0:
                print(f"Processed {processed_count} points...")

        except Exception as e:
            import traceback
            print(f"[WARN] Failed at {lat},{lon}: {e}")
            traceback.print_exc()

    # Save JSON for Frontend
    with open(OUTPUT_FILE_JSON, "w", newline="") as f:
        json.dump(predictions, f, indent=2)

    print(f"[OK] Hourly prediction completed at {timestamp}")
    print(f"   Processed (Land): {processed_count}")
    print(f"   Skipped (Ocean): {skipped_count}")
    print(f"[OK] Saved to {OUTPUT_FILE_CSV} and {OUTPUT_FILE_JSON}")


if __name__ == "__main__":
    run_pipeline()
