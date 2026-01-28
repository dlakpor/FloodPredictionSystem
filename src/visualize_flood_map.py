import json
import folium
import pandas as pd


def risk_color(risk):
    if risk == "High":
        return "red"
    elif risk == "Moderate":
        return "orange"
    else:
        return "green"


def create_flood_map():
    with open("data/latest_grid_predictions.json", "r") as f:
        data = json.load(f)

    # Flatten JSON
    records = []
    for item in data:
        records.append({
            "lat": item["latitude"],
            "lon": item["longitude"],
            "flood_risk": item["prediction"]["flood_risk"],
            "flood_probability": item["prediction"]["flood_probability"]
        })

    df = pd.DataFrame(records)

    # Center map on Cyprus
    m = folium.Map(location=[35.0, 33.0], zoom_start=8)

    for _, row in df.iterrows():
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=6,
            color=risk_color(row["flood_risk"]),
            fill=True,
            fill_opacity=0.7,
            popup=(
                f"Risk: {row['flood_risk']}<br>"
                f"Probability: {row['flood_probability']:.2f}"
            )
        ).add_to(m)

    m.save("data/cyprus_flood_risk_map.html")
    print("🗺 Flood risk map saved: data/cyprus_flood_risk_map.html")


if __name__ == "__main__":
    create_flood_map()
