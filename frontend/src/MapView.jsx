// src/MapView.jsx
import { useEffect, useMemo, useState } from "react";
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Tooltip,
  useMap,
  useMapEvents,
  Marker,
  Popup,
  Rectangle,
  Polygon
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

// Fix default marker icon issue in React Leaflet
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

const northCyprusCenter = [35.33, 33.25];
const northCyprusBounds = [
  [35.00, 32.20],
  [35.80, 34.85],
];

function FlyToLocation({ location, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (!location || typeof location.lat !== "number" || typeof location.lon !== "number") return;
    // Use provided zoom or default to 14 for search, 11 for sidebar (50% zoom)
    const targetZoom = location.zoom || zoom || 14;
    map.flyTo([location.lat, location.lon], targetZoom, {
      duration: 1.5, // Smooth 1.5 second transition
      easeLinearity: 0.25
    });
  }, [location, zoom, map]);
  return null;
}

function ZoomToPoint({ point, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (!point) return;
    map.flyTo([point.lat, point.lon], zoom || 11, {
      duration: 1.5,
      easeLinearity: 0.25
    });
  }, [point, zoom, map]);
  return null;
}

function MapClickHandler({ onMapClick }) {
  useMapEvents({
    click: (e) => onMapClick(e.latlng),
  });
  return null;
}

function FitToGrid({ grid }) {
  const map = useMap();
  useEffect(() => {
    if (grid && grid.length > 0) {
      const lats = grid.map((p) => Number(p.lat));
      const lons = grid.map((p) => Number(p.lon));
      const minLat = Math.min(...lats);
      const maxLat = Math.max(...lats);
      const minLon = Math.min(...lons);
      const maxLon = Math.max(...lons);
      map.fitBounds([[minLat, minLon], [maxLat, maxLon]], { padding: [30, 30] });
    } else {
      map.fitBounds(northCyprusBounds, { padding: [30, 30] });
    }
  }, [grid, map]);
  return null;
}

function MapView({ onSelectPoint, selectedPoint, flyToLocation, onGridLoaded, grid, status, loadGrid, refreshNow }) {

  const [filter, setFilter] = useState("All");
  const [mapMode, setMapMode] = useState("satellite"); // 'satellite' or 'standard'
  const [selected, setSelected] = useState(null);
  const [customMarker, setCustomMarker] = useState(null);

  // Sync internal selection with parent prop
  useEffect(() => {
    setSelected(selectedPoint);
    if (!selectedPoint) setCustomMarker(null);
  }, [selectedPoint]);

  // Click handler for arbitrary locations
  const handleMapClick = async (latlng) => {
    // Clear any previous selection when clicking on map
    if (onSelectPoint) onSelectPoint(null);

    setCustomMarker(latlng);
    const tempSelected = {
      lat: latlng.lat,
      lon: latlng.lng,
      flood_risk: "Loading...",
      flood_probability: 0,
      predicted_rainfall_mm: 0,
      isCustom: true
    };
    setSelected(tempSelected);
    if (onSelectPoint) onSelectPoint(tempSelected);

    try {
      const res = await fetch(`/api/predict-location?lat=${latlng.lat}&lon=${latlng.lng}`);
      if (!res.ok) throw new Error("Prediction failed");
      const data = await res.json();
      const updated = {
        ...data,
        lat: data.location.lat,
        lon: data.location.lon,
        flood_risk: data.prediction.flood_risk,
        flood_probability: data.prediction.flood_probability,
        predicted_rainfall_mm: data.prediction.predicted_rainfall_mm,
        isCustom: true
      };
      setSelected(updated);
      if (onSelectPoint) onSelectPoint(updated);
    } catch (e) {
      console.error(e);
      setSelected(prev => ({ ...prev, flood_risk: "Error", isCustom: true }));
    }
  };

  const filteredGrid = useMemo(() => {
    let base = grid;
    if (filter === "High") base = base.filter((p) => p.flood_risk === "High");
    else if (filter === "Moderate+High")
      base = base.filter((p) => p.flood_risk === "High" || p.flood_risk === "Moderate");

    return base;
  }, [grid, filter]);

  const statsCount = useMemo(() => {
    let low = 0, mod = 0, high = 0;
    for (const p of filteredGrid) {
      if (p.flood_risk === "High") high++;
      else if (p.flood_risk === "Moderate") mod++;
      else low++;
    }
    return { low, mod, high };
  }, [filteredGrid]);

  return (
    <div style={{ height: "100%", width: "100%", display: "flex", gap: '20px' }}>

      {/* Dashboard Side Panel */}
      <div style={{ width: '300px', flexShrink: 0, display: 'flex', flexDirection: 'column', gap: '15px' }}>
        <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 'bold' }}>Cyprus Flood Risk Dashboard</h3>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={() => {
              loadGrid();
              // Force map to reset to default view by clearing selection
              if (onSelectPoint) onSelectPoint(null);
            }}
            style={{ flex: 1, background: '#0b5ed7', color: 'white', border: 'none', padding: '10px', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
            Reload
          </button>
          <button onClick={refreshNow} style={{ flex: 1, background: '#198754', color: 'white', border: 'none', padding: '10px', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>Refresh Now</button>
        </div>

        <div style={{ fontSize: '13px', lineHeight: '1.6' }}>
          <div><b>Status:</b> {status.loading ? 'Updating...' : 'Live'}</div>
          <div><b>Model:</b> <span style={{ textTransform: 'uppercase', color: '#1a73e8', fontWeight: 'bold' }}>{status.activeModel || 'N/A'}</span></div>
          <div><b>Points:</b> {filteredGrid.length}</div>
          <div><b>Last update:</b> {status.lastUpdated ? status.lastUpdated.toLocaleString() : 'N/A'}</div>
          <div style={{ fontSize: '11px', color: '#666', marginTop: '5px', fontStyle: 'italic' }}>
            Note: "Refresh Now" updates LIVE weather (slower). "Reload" updates model logic (fast).
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
          <RiskBox label="Low" count={statsCount.low} height="40px" />
          <RiskBox label="Moderate" count={statsCount.mod} height="40px" />
          <RiskBox label="High" count={statsCount.high} height="40px" />
        </div>

        <div style={{ marginBottom: '10px' }}>
          <label style={{ fontSize: '14px', fontWeight: 'bold', display: 'block', marginBottom: '8px' }}>Map Theme</label>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => setMapMode('satellite')}
              style={{
                flex: 1,
                padding: '8px',
                fontSize: '12px',
                background: mapMode === 'satellite' ? '#0b5ed7' : 'white',
                color: mapMode === 'satellite' ? 'white' : '#666',
                border: '1px solid #dee2e6',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: '600',
                transition: 'all 0.2s'
              }}
            >Satellite</button>
            <button
              onClick={() => setMapMode('standard')}
              style={{
                flex: 1,
                padding: '8px',
                fontSize: '12px',
                background: mapMode === 'standard' ? '#0b5ed7' : 'white',
                color: mapMode === 'standard' ? 'white' : '#666',
                border: '1px solid #dee2e6',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: '600',
                transition: 'all 0.2s'
              }}
            >Standard</button>
          </div>
        </div>

        <div>
          <label style={{ fontSize: '14px', fontWeight: 'bold', display: 'block', marginBottom: '5px' }}>Flood Filter</label>
          <select value={filter} onChange={(e) => setFilter(e.target.value)} style={{ width: '100%', padding: '8px', border: '1px solid #dee2e6', borderRadius: '4px' }}>
            <option value="All">All predictions</option>
            <option value="Moderate+High">Moderate & High</option>
            <option value="High">High only</option>
          </select>
        </div>

        <div>
          <label style={{ fontSize: '14px', fontWeight: 'bold', display: 'block', marginBottom: '5px' }}>Legend</label>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px', fontSize: '13px' }}>
            <LegendItem color="#198754" label="Low" />
            <LegendItem color="#ffc107" label="Moderate" />
            <LegendItem color="#dc3545" label="High" />
          </div>
        </div>

        <div style={{ marginTop: '10px' }}>
          <label style={{ fontSize: '14px', fontWeight: 'bold', display: 'block', marginBottom: '5px' }}>Selected point</label>
          <div style={{ fontSize: '13px', color: '#666' }}>
            {selected ? `Lat: ${selected.lat.toFixed(3)}, Lon: ${selected.lon.toFixed(3)}` : 'Click a dot on the map.'}
          </div>
        </div>
      </div>

      {/* Map View */}
      <div style={{ flex: 1, position: 'relative', border: '1px solid #dee2e6', borderRadius: '4px', overflow: 'hidden' }}>
        <MapContainer
          center={northCyprusCenter}
          zoom={10}
          style={{ height: "100%", width: "100%" }}
          maxBounds={northCyprusBounds}
          maxBoundsViscosity={1.0}
        >
          <MapClickHandler onMapClick={handleMapClick} />
          {flyToLocation && <FlyToLocation location={flyToLocation} />}
          <FitToGrid grid={filteredGrid} />
          {mapMode === 'satellite' ? (
            <>
              {/* Satellite Layer */}
              <TileLayer
                url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                attribution='&copy; <a href="https://www.esri.com/">Esri</a>'
              />
              {/* Transparent Labels Overlay */}
              <TileLayer
                url="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"
                opacity={0.8}
              />
            </>
          ) : (
            <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          )}

          {/* Dynamic Color Overlay for Selected Area */}
          {(() => {
            const current = selectedPoint || selected;
            if (!current || isNaN(Number(current.lat)) || isNaN(Number(current.lon))) return null;

            const lat = Number(current.lat);
            const lon = Number(current.lon);
            const halfStep = 0.0025; // Reduced by another 50%

            const bounds = [
              [lat - halfStep, lon - halfStep],
              [lat + halfStep, lon + halfStep]
            ];

            // Determine overlay color based on flood risk (matching grid point colors)
            let overlayColor = '#198754'; // Default green for Low
            if (current.flood_risk === 'High') {
              overlayColor = '#ff0000'; // Red
            } else if (current.flood_risk === 'Moderate') {
              overlayColor = '#ffc107'; // Yellow/Orange
            }

            return (
              <Rectangle
                bounds={bounds}
                pathOptions={{
                  fillColor: overlayColor,
                  fillOpacity: 0.25,
                  color: overlayColor,
                  weight: 2,
                  opacity: 0.5
                }}
              />
            );
          })()}


          {/* Center Marker inside the shaded grid */}
          {((selected || flyToLocation)) && (
            <CircleMarker
              center={[
                Number(selected?.lat || flyToLocation?.lat),
                Number(selected?.lon || flyToLocation?.lon)
              ]}
              radius={11} // Slightly smaller
              pathOptions={{
                color: 'white',
                fillColor: '#1b806a',
                fillOpacity: 1,
                weight: 4
              }}
            >
              <Tooltip permanent direction="top" offset={[0, -10]}>
                <span style={{ fontWeight: 'bold' }}>Selected Grid</span>
              </Tooltip>
            </CircleMarker>
          )}

          {customMarker && (
            <Marker position={customMarker}>
              <Popup>Selected Location</Popup>
            </Marker>
          )}

          {filteredGrid.map((p, i) => {
            const isSelected = (selected && selected.lat === p.lat && selected.lon === p.lon);
            const isHigh = p.flood_risk === "High";

            return (
              <CircleMarker
                key={i}
                center={[Number(p.lat), Number(p.lon)]}
                radius={isSelected ? 14 : (isHigh ? 12 : 6)}
                fill
                fillColor={["High", "high"].includes(p.flood_risk) ? "#ff0000" : (["Moderate", "moderate"].includes(p.flood_risk) ? "#ffc107" : "#198754")}
                fillOpacity={isHigh ? 0.9 : 0.8}
                stroke={isSelected || isHigh}
                color={isHigh ? "white" : "white"}
                weight={isSelected ? 4 : (isHigh ? 2 : 1)}
                eventHandlers={{
                  click: (e) => {
                    L.DomEvent.stopPropagation(e);
                    setSelected(p);
                    setCustomMarker(null);
                    if (onSelectPoint) onSelectPoint(p);
                  },
                }}
              >
                <Tooltip>
                  <b>{p.flood_risk} Risk</b><br />
                  Action: {p.recommended_action || p.prediction?.recommended_action || "Monitor"}<br />
                  Prob: {(Number(p.flood_probability) * 100).toFixed(1)}%<br />
                  Rain: {Number(p.predicted_rainfall_mm).toFixed(3)} mm
                </Tooltip>
              </CircleMarker>
            );
          })}
        </MapContainer>
      </div>
    </div >
  );
}

function RiskBox({ label, count }) {
  return (
    <div style={{ border: '1px solid #dee2e6', borderRadius: '4px', padding: '8px', textAlign: 'center', background: '#f8f9fa' }}>
      <div style={{ fontSize: '11px', color: '#666', marginBottom: '4px' }}>{label}</div>
      <div style={{ fontSize: '18px', fontWeight: 'bold' }}>{count}</div>
    </div>
  );
}

function LegendItem({ color, label }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <span style={{ width: '12px', height: '12px', background: color, borderRadius: '2px' }}></span>
      <span>{label}</span>
    </div>
  );
}

export default MapView;
