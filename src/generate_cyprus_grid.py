import json
import os
import numpy as np

OUTPUT_FILE = "data/cyprus_grid_points.json"

def generate_grid():
    # ✅ Comprehensive North Cyprus bounding box
    # Covers from the West (32.2) to the tip of Karpaz (34.6)
    lat_min, lat_max = 35.00, 35.70
    lon_min, lon_max = 32.20, 34.65

    # Step size that balances coverage and speed (approx 5-6km spacing)
    step = 0.04

    grid = []
    for lat in np.arange(lat_min, lat_max, step):
        for lon in np.arange(lon_min, lon_max, step):
            grid.append({
                "lat": round(float(lat), 5),
                "lon": round(float(lon), 5)
            })

    os.makedirs("data", exist_ok=True)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(grid, f, indent=2)

    print(f"✅ Generated {len(grid)} grid points covering all of North Cyprus.")

if __name__ == "__main__":
    generate_grid()
