# src/grid_weather_to_api.py

import json
import os
from datetime import datetime
from math import sin, cos
import random

# ---------------------------
# PATHS / FILES
# ---------------------------
DATA_DIR = "data"
GRID_POINTS_FILE = os.path.join(DATA_DIR, "cyprus_grid_points.json")

LATEST_OUTPUT_FILE = os.path.join(DATA_DIR, "latest_grid_predictions.json")

# North Cyprus bounding box (safety filter)
LAT_MIN, LAT_MAX = 35.05, 35.75
LON_MIN, LON_MAX = 32.20, 34.85


# ---------------------------
# RISK CLASSIFICATION
# ---------------------------
def classify_risk(rainfall_mm: float) -> tuple[float, str]:
    """
    Convert rainfall into a probability and a risk label.
    These thresholds are reasonable for a demo flood-risk map.
    """
    # probability 0..1 (simple scaled mapping)
    prob = max(0.0, min(1.0, rainfall_mm / 40.0))

    if rainfall_mm >= 25:
        risk = "High"
    elif rainfall_mm >= 10:
        risk = "Moderate"
    else:
        risk = "Low"

    return prob, risk


# ---------------------------
# BASELINE PREDICTOR (VARIES BY LOCATION)
# ---------------------------
def predict_rainfall_mm(lat: float, lon: float) -> float:
    """
    A deterministic-ish spatial predictor (varies by lat/lon),
    with light noise so dots differ.
    Replace this with your real ML model later.
    """

    # Normalize lat/lon into 0..1 range within North Cyprus bbox
    lat_n = (lat - LAT_MIN) / (LAT_MAX - LAT_MIN)
    lon_n = (lon - LON_MIN) / (LON_MAX - LON_MIN)

    # Create a "rain band" pattern + coastal effect style variation
    # (just a realistic-looking spatial field)
    wave = 8.0 * (0.5 + 0.5 * sin(3.5 * lon_n * 3.14159) * cos(2.5 * lat_n * 3.14159))
    gradient = 10.0 * lat_n  # slightly higher northward
    hotspot = 12.0 * (1.0 / (1.0 + ((lat_n - 0.55) ** 2 + (lon_n - 0.60) ** 2) * 25.0))

    noise = random.uniform(-1.2, 1.2)

    rainfall = max(0.0, 2.0 + wave + gradient + hotspot + noise)
    return round(rainfall, 3)


# ---------------------------
# GRID LOADING
# ---------------------------
def load_grid_points() -> list[dict]:
    if not os.path.exists(GRID_POINTS_FILE):
        raise FileNotFoundError(
            f"Grid file not found: {GRID_POINTS_FILE}\n"
            f"Make sure you generated it and it's in the data folder."
        )

    with open(GRID_POINTS_FILE, "r", encoding="utf-8") as f:
        grid = json.load(f)

    def is_land(lat: float, lon: float) -> bool:
        """
        Rough North Cyprus land mask.
        Simple, explainable, thesis-safe.
        """
        return (
            35.05 <= lat <= 35.45 and
            32.60 <= lon <= 34.60
        )

    filtered = []
    for p in grid:
        lat = float(p["lat"])
        lon = float(p["lon"])

        if (
            LAT_MIN <= lat <= LAT_MAX and
            LON_MIN <= lon <= LON_MAX and
            is_land(lat, lon)
        ):
            filtered.append({"lat": lat, "lon": lon})

    print(f"Loaded {len(filtered)} North Cyprus land grid points")
    return filtered


    # Polygon defining North Cyprus (Approximate)
    NORTH_CYPRUS_POLYGON = [
        (35.17, 32.90), (35.40, 32.90), (35.42, 33.60),
        (35.58, 34.20), (35.70, 34.60), (35.55, 34.55),
        (35.40, 34.10), (35.10, 33.95), (35.10, 33.90),
        (35.00, 33.70), (35.12, 33.35), (35.17, 32.90)
    ]

    def is_point_in_polygon(lat, lon, polygon):
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

    filtered = []
    for p in grid:
        lat = float(p["lat"])
        lon = float(p["lon"])

        if is_point_in_polygon(lat, lon, NORTH_CYPRUS_POLYGON):
            filtered.append({"lat": lat, "lon": lon})

    print(f"Loaded {len(filtered)} North Cyprus land grid points (Filtered by Polygon)")
    return filtered


# ---------------------------
# PIPELINE
# ---------------------------
def generate_predictions() -> list[dict]:
    grid = load_grid_points()
    predictions = []

    for p in grid:
        lat = p["lat"]
        lon = p["lon"]

        rainfall = predict_rainfall_mm(lat, lon)
        prob, risk = classify_risk(rainfall)

        predictions.append(
            {
                "lat": round(lat, 5),
                "lon": round(lon, 5),
                "predicted_rainfall_mm": float(rainfall),
                "flood_probability": float(round(prob, 6)),
                "flood_risk": risk,
            }
        )

    return predictions


def save_predictions(predictions: list[dict]) -> tuple[str, str]:
    os.makedirs(DATA_DIR, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
    timestamped_file = os.path.join(DATA_DIR, f"grid_predictions_{timestamp}.json")

    # Save timestamped (history)
    with open(timestamped_file, "w", encoding="utf-8") as f:
        json.dump(predictions, f, indent=2)

    # Save latest (frontend should read this)
    with open(LATEST_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(predictions, f, indent=2)

    return timestamped_file, LATEST_OUTPUT_FILE


def main():
    preds = generate_predictions()

    # Quick stats
    low = sum(1 for p in preds if p["flood_risk"] == "Low")
    mod = sum(1 for p in preds if p["flood_risk"] == "Moderate")
    high = sum(1 for p in preds if p["flood_risk"] == "High")

    ts_file, latest_file = save_predictions(preds)

    print(f"✅ Generated predictions for {len(preds)} points (North Cyprus only)")
    print(f"   Low={low}  Moderate={mod}  High={high}")
    print(f"✅ Saved history: {ts_file}")
    print(f"✅ Updated latest: {latest_file}")
    print(f"✅ Sample: {preds[0] if preds else 'NO DATA'}")


if __name__ == "__main__":
    main()
