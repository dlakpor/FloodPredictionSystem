# Data Directory

This folder contains all the datasets, grid definitions, and prediction outputs used by the North Cyprus Flood Prediction System.

## Directory Structure

### 1. Raw Weather Data (ERA5)
- **`.nc` files (NetCDF)**: Monthly weather data files fetched from the Copernicus Climate Data Store (ERA5-Land). These contain variables like total precipitation (`tp`) and 2m temperature (`t2m`).
- **`era5_2023_01.zip`**: Compressed raw data for archival.
- **`extracted/`**: Directory containing unzipped or processed individual weather files.

### 2. Processed Datasets (CSV)
- **`era5_combined.csv`**: The master dataset containing hourly weather observations for all grid points across the historical period.
- **`era5_daily.csv`**: Hourly data aggregated into daily summaries (max temp, total rain).
- **`era5_labeled.csv`**: Data processed to include flood incidence labels, used for training the classifier and regressor.
- **`features_for_ml.csv`**: The final feature-engineered dataset (including lags, rolling averages, and topographic metadata) used for ML model training.

### 3. Grid & Geometry
- **`cyprus_grid_points.json`**: Defines the mesh of latitude/longitude points covering North Cyprus. These are the fixed locations where predictions are generated.
- **`geo/`**: Contains geographic definitions (polygons) used for filtering land vs. sea points.

### 4. Prediction Outputs
- **`latest_grid_predictions.json`**: The primary data source for the web dashboard. It stores the most recent risk assessments (Low/Moderate/High) and rainfall values for every active grid point.
- **`grid_predictions_TIMESTAMP.json`**: Periodic snapshots/backups of the grid state.
- **`hourly_predictions.csv`**: A historical log of all predictions made by the automated pipeline for auditing and trend analysis.

### 5. Visualizations
- **`cyprus_flood_risk_map.html`**: A standalone interactive HTML map (Leaflet/Folium based) visualizing the spatial distribution of flood risk.

---
**Note:** Large files (`.csv` > 100MB) are typically ignored by version control. Ensure you have the localized copy if training new models.
