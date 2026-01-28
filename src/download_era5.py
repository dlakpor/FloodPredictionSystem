import cdsapi
import os
import time

# Create output directory
os.makedirs("../data", exist_ok=True)

# CDS API client
c = cdsapi.Client()

# TRNC / North Cyprus bounding box
area = [36.7, 32.2, 34.5, 35.8]  # North/West/South/East

# Years and months to download
years = ["2023", "2024"]     # You may edit this
months = [f"{m:02d}" for m in range(1, 13)]  # 01–12

def download_month(year, month):
    filename = f"../data/era5_{year}_{month}.nc"

    # Skip already downloaded files
    if os.path.exists(filename):
        print(f"Already exists: {filename}")
        return

    print(f"\n=== Downloading {year}-{month} ===")

    try:
        c.retrieve(
            "reanalysis-era5-land",
            {
                "format": "netcdf",
                "variable": [
                    "total_precipitation",
                    "soil_moisture_level_1",
                    "2m_temperature",
                ],
                "year": year,
                "month": month,
                "day": [f"{d:02d}" for d in range(1, 32)],
                "time": [f"{h:02d}:00" for h in range(24)],
                "area": area,
            },
            filename
        )
        print(f"Completed: {filename}")

    except Exception as e:
        print(f"Error downloading {year}-{month}: {e}")
        print("Retrying in 15 seconds...")
        time.sleep(15)
        download_month(year, month)  # retry automatically


# Main download loop
for year in years:
    for month in months:
        download_month(year, month)

print("\n All downloads finished!")
