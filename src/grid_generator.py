import numpy as np

def generate_cyprus_grid(step=0.08):
    # Cyprus bounding box
    lat_min, lat_max = 34.5, 35.7
    lon_min, lon_max = 32.0, 34.1

    grid = []
    lat = lat_min
    while lat <= lat_max:
        lon = lon_min
        while lon <= lon_max:
            grid.append((round(lat, 2), round(lon, 2)))
            lon += step
        lat += step

    return grid

if __name__ == "__main__":
    grid = generate_cyprus_grid()
    print(f"Generated {len(grid)} grid points")
    print(grid[:10])
