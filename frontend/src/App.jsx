import { useState, useMemo, useEffect } from "react";
import "./App.css";
import MapView from "./MapView";
import Header from "./components/Header";
import Sidebar from "./components/Sidebar";
import StatsPanel from "./components/StatsPanel";
import { jsPDF } from "jspdf";

// Cache buster - verify latest code is loaded
console.log("🔄 App loaded - Ocean Filter v4.0 (User Feedback) - " + new Date().toISOString());

function App() {
  // Application State
  const [gridData, setGridData] = useState([]);
  const [selectedPoint, setSelectedPoint] = useState(null);

  const [status, setStatus] = useState({
    loading: true,
    error: null,
    lastUpdated: null,
  });

  const [searchQuery, setSearchQuery] = useState("");
  const [searchResult, setSearchResult] = useState(null);
  const [selectedModel, setSelectedModel] = useState(localStorage.getItem("selected_model") || "rf");

  // 1. Clean Grid Data - Polygon Based Filtering (The "Better Fix")
  // Ray-Casting Algorithm to strictly keep points INSIDE the North Cyprus landmass
  const cleanGrid = useMemo(() => {

    // Polygon defining the approximate border of North Cyprus (High Fidelity v4 - User Feedback)
    // Aggressive filtering for Kormakitis Tip, Famagusta Bay, and Karpaz Tip
    const ncPolygon = [
      // West Coast & Morphou Bay
      [35.08, 32.75], // Lefke Inland
      [35.15, 32.85], // Morphou West Coast
      [35.22, 32.94], // Morphou Bay Deep
      [35.32, 32.93], // Morphou Bay North / Kormakitis West

      // Cape Kormakitis (Circle 1 Fix: Shaved Tip)
      [35.40, 32.95], // Shaved Tip South-West a bit
      [35.36, 33.10], // Kormakitis East

      // Kyrenia Coast
      [35.34, 33.25], // Lapta/Alsancak
      [35.33, 33.35], // Kyrenia Harbor
      [35.34, 33.55], // Catalkoy / Esentepe West

      // Esentepe & Kantara
      [35.38, 33.75], // Esentepe Coast
      [35.42, 33.95], // Tatlisu
      [35.47, 34.08], // Kaplica / Kantara North

      // Karpaz Peninsula - North Side
      [35.54, 34.22], // Yeni Erenkoy
      [35.60, 34.38], // Dipkarpaz North
      [35.67, 34.54], // Zafer Burnu (Tip North) - Retracted
      [35.69, 34.58], // The Absolute Tip - Retracted West (Circle 3 Fix)

      // Karpaz Peninsula - South Side
      [35.65, 34.58], // Tip South - Retracted West
      [35.58, 34.50], // Dipkarpaz South - Shaved
      [35.52, 34.35], // Kaleburnu
      [35.45, 34.20], // Balalan Coast
      [35.38, 34.10], // Bogaz North

      // Famagusta Bay (Circle 2 Fix: Deep Cut Inland)
      [35.28, 33.97], // Iskele / Long Beach - Pushed West
      [35.20, 33.92], // Glapsides - Pushed West
      [35.12, 33.94], // Famagusta Port - Tightened

      // The Green Line (Border)
      [35.09, 33.92], // Varosha South limit
      [35.10, 33.70], // Mesaoria Border East
      [35.12, 33.50], // Nicosia North Border
      [35.16, 33.35], // Nicosia West Buffer
      [35.14, 33.15], // Morphou Plain Border
      [35.10, 32.90]  // Back to Lefke area
    ];

    const isPointInPolygon = (lat, lon, poly) => {
      let inside = false;
      for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
        const xi = poly[i][0], yi = poly[i][1];
        const xj = poly[j][0], yj = poly[j][1];

        // Check if point is on the line segment
        const intersect = ((yi > lon) !== (yj > lon)) &&
          (lat < (xj - xi) * (lon - yi) / (yj - yi) + xi);
        if (intersect) inside = !inside;
      }
      return inside;
    };

    return gridData.filter(p => {
      const lat = Number(p.lat);
      const lon = Number(p.lon);
      const name = (p.location_name || "").toLowerCase();

      if (name.includes("sea") || name.includes("ocean")) return false;

      // Note: Polygon is [Lat, Lon]. x=lat, y=lon in our check.
      return isPointInPolygon(lat, lon, ncPolygon);
    });
  }, [gridData]);

  // 2. Sidebar Locations: Sorted by probability
  const riskLocations = useMemo(() => {
    return [...cleanGrid].sort((a, b) => b.flood_probability - a.flood_probability);
  }, [cleanGrid]);

  // 2. Format Location Name (Client-side heuristic if API name is missing)
  const formatLocationName = (p) => {
    if (p.location_name && p.location_name !== "Unknown") return p.location_name;

    // Heuristic naming based on rough coordinates
    const lat = p.lat, lon = p.lon;
    if (lon < 33.0) return `Lefke / Guzelyurt Region (${lat.toFixed(2)}, ${lon.toFixed(2)})`;
    if (lon >= 33.0 && lon < 33.5 && lat > 35.25) return `Kyrenia West (${lat.toFixed(2)}, ${lon.toFixed(2)})`;
    if (lon >= 33.0 && lon < 33.5 && lat <= 35.25) return `Nicosia / Guzelyurt (${lat.toFixed(2)}, ${lon.toFixed(2)})`;
    if (lon >= 33.5 && lon < 33.95 && lat > 35.3) return `Kyrenia East / Esentepe (${lat.toFixed(2)}, ${lon.toFixed(2)})`;
    if (lon >= 33.5 && lon < 33.95 && lat <= 35.3) return `Mesarya / Nicosia East (${lat.toFixed(2)}, ${lon.toFixed(2)})`;
    if (lon >= 33.95 && lat <= 35.35) return `Famagusta Region (${lat.toFixed(2)}, ${lon.toFixed(2)})`;
    if (lon >= 33.95 && lat > 35.35) return `Iskele / Karpaz (${lat.toFixed(2)}, ${lon.toFixed(2)})`;

    return `Location (${p.lat.toFixed(3)}, ${p.lon.toFixed(3)})`;
  };

  // Helper: load latest grid from API
  const loadGrid = async (model = selectedModel) => {
    try {
      console.log(`🔄 Fetching grid data for model: ${model}`);
      setStatus((s) => ({ ...s, loading: true, error: null }));
      const res = await fetch(`/api/grid/latest?model=${model}`);
      const json = await res.json();
      if (!res.ok) throw new Error(json?.detail || `HTTP ${res.status}`);
      if (json?.status !== "success") throw new Error(json?.message || "Grid API returned non-success status");

      setGridData(json.data || []);
      setStatus({
        loading: false,
        error: null,
        lastUpdated: new Date(),
        activeModel: json.model_applied || model,
        generatedAt: json.generated_at_utc
      });
    } catch (err) {
      console.warn("Grid load error:", err);
      setStatus(prev => ({ ...prev, loading: false, error: err?.message || String(err) }));
      // Retry once after 3 seconds if it failed (helps if backend is just starting)
      setTimeout(() => {
        if (gridData.length === 0) loadGrid(model);
      }, 3000);
    }
  };

  // refresh pipeline then reload grid
  const refreshNow = async () => {
    try {
      setStatus((s) => ({ ...s, loading: true, error: null }));
      const r = await fetch(`/api/grid/refresh?model=${selectedModel}`, { method: "POST" });
      if (!r.ok) {
        const errJson = await r.json().catch(() => ({}));
        throw new Error(errJson?.detail?.message || errJson?.detail || `Refresh failed (HTTP ${r.status})`);
      }
      await loadGrid();
    } catch (err) {
      setStatus({ loading: false, error: err?.message || String(err), lastUpdated: null });
    }
  };

  // Unified auto-load + refresh logic (Handles Model Changes)
  useEffect(() => {
    loadGrid(selectedModel);
    const id = setInterval(() => loadGrid(selectedModel), 5 * 60 * 1000);
    return () => clearInterval(id);
  }, [selectedModel]);

  // INSTANT UPDATE: Sync selected point with new grid data when model switches
  useEffect(() => {
    if (selectedPoint && gridData.length > 0) {
      // Find the updated version of the selected point in the new grid
      const updatedPoint = gridData.find(p =>
        Math.abs(Number(p.lat) - Number(selectedPoint.lat)) < 0.001 &&
        Math.abs(Number(p.lon) - Number(selectedPoint.lon)) < 0.001
      );

      if (updatedPoint) {
        // preserve weather/location info but strictly update prediction flags
        setSelectedPoint(prev => ({
          ...prev, // keep existing weather info
          ...updatedPoint, // overwrite with new prediction (risk, prob, rain)
          model_used: selectedModel,
          isLoadingDetails: false
        }));
      }
    }
  }, [gridData]); // Run whenever the grid refreshes (which happens on model switch)

  // Background Refetch for LIVE weather (Optional, keeps data fresh)
  useEffect(() => {
    if (selectedPoint && selectedPoint.model_used !== selectedModel) {
      // Silent background refresh for weather
      fetch(`/api/predict-location?lat=${selectedPoint.lat}&lon=${selectedPoint.lon}&model=${selectedModel}`)
        .then(res => res.json())
        .then(data => {
          setSelectedPoint(prev => ({ ...prev, ...data }));
        })
        .catch(console.error);
    }
  }, [selectedModel]);

  // Handle model change and show status
  const handleModelChange = (model) => {
    setSelectedModel(model);
    localStorage.setItem("selected_model", model);
    // Optionally trigger a full grid refresh? 
    // For now, just instant update of selected point is enough.
    // User can click "Refresh Now" for full grid.
  };

  // 4. Search Handler
  const searchLocation = async () => {
    if (!searchQuery.trim()) return;
    try {
      // Clear previous selection before searching
      setSelectedPoint(null);
      setSearchResult(null);

      const res = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery)}&bounded=1&viewbox=32.2,35.8,34.9,35.0`
      );
      const data = await res.json();
      if (data.length === 0) {
        alert("Location not found in North Cyprus.");
        return;
      }
      const loc = {
        lat: parseFloat(data[0].lat),
        lon: parseFloat(data[0].lon),
        name: data[0].display_name,
        zoom: 14
      };
      setSearchResult(loc);

      // Fetch detailed weather/risk for this search result
      try {
        const resPred = await fetch(`/api/predict-location?lat=${loc.lat}&lon=${loc.lon}&model=${selectedModel}`);
        if (resPred.ok) {
          const predData = await resPred.json();
          setSelectedPoint({
            ...predData,
            lat: loc.lat,
            lon: loc.lon,
            location_name: loc.name,
            temp_c: Math.round(predData.temp_c),
            flood_risk: predData.prediction.flood_risk,
            flood_probability: predData.prediction.flood_probability,
            predicted_rainfall_mm: predData.prediction.predicted_rainfall_mm
          });
        }
      } catch (e) {
        console.warn("Prediction fetch failed for search result:", e);
      }
    } catch (err) {
      console.error("Search failed:", err);
    }
  };

  // 5. Download Report as PDF
  const downloadPDF = () => {
    if (!selectedPoint) return;
    const doc = new jsPDF();
    const name = formatLocationName(selectedPoint);
    const date = new Date().toLocaleString();

    // Header Background
    doc.setFillColor(11, 94, 215);
    doc.rect(0, 0, 210, 45, 'F');

    // Title (H1 style)
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(22);
    doc.setFont("helvetica", "bold");
    doc.text("North Cyprus Flood Prediction", 15, 20);

    // Subtitle (H2 style)
    doc.setFontSize(14);
    doc.setFont("helvetica", "normal");
    doc.text("Prediction Analysis Report", 15, 30);

    doc.setTextColor(0, 0, 0);
    doc.setFontSize(10);
    doc.text(`Generated: ${date}`, 155, 55);

    doc.setFontSize(16);
    doc.setFont("helvetica", "bold");
    doc.text("Location Details", 15, 70);
    doc.setFontSize(12);
    doc.setFont("helvetica", "normal");
    doc.text(`Area: ${name}`, 15, 80);
    doc.text(`Coordinates: ${selectedPoint.lat.toFixed(4)}, ${selectedPoint.lon.toFixed(4)}`, 15, 87);

    doc.setFontSize(16);
    doc.setFont("helvetica", "bold");
    doc.text("Weather Analysis", 15, 105);
    doc.setFontSize(12);
    doc.setFont("helvetica", "normal");
    doc.text(`Temperature: ${selectedPoint.temp_c}°C`, 15, 115);
    doc.text(`Weather: ${selectedPoint.weather_summary}`, 15, 122);
    doc.text(`Predicted Rainfall: ${selectedPoint.predicted_rainfall_mm} mm`, 15, 129);

    doc.setFontSize(16);
    doc.setFont("helvetica", "bold");
    doc.text("Flood Risk Assessment", 15, 145);
    doc.setFontSize(14);
    doc.setTextColor(selectedPoint.flood_risk === 'High' ? 211 : 0, 47, 47);
    doc.text(`Current Risk: ${selectedPoint.flood_risk}`, 15, 155);
    doc.setTextColor(0, 0, 0);
    doc.setFontSize(12);
    doc.setFont("helvetica", "normal");
    doc.text(`Probability: ${(selectedPoint.flood_probability * 100).toFixed(1)}%`, 15, 162);
    doc.text(`Action: ${selectedPoint.recommended_action || selectedPoint.prediction?.recommended_action || 'Monitor'}`, 15, 169);

    doc.setFontSize(16);
    doc.setFont("helvetica", "bold");
    doc.text("Future Flood Outlook", 15, 185);
    doc.setFontSize(11);
    doc.setFont("helvetica", "normal");
    const horizons = selectedPoint.prediction?.future_horizons || {};
    let yPos = 195;
    ['24h', '48h', '72h'].forEach(h => {
      const data = horizons[h];
      if (data) {
        doc.text(`> ${h} Forecast (${data.time}): ${data.risk} Risk (${data.rainfall_mm}mm rain)`, 15, yPos);
        yPos += 7;
      }
    });

    doc.save(`Flood_Report_${name.replace(/\W+/g, '_')}.pdf`);
  };

  // 6. Download Report as CSV
  const downloadCSV = () => {
    if (!selectedPoint) return;
    const name = formatLocationName(selectedPoint);
    const horizons = selectedPoint.prediction?.future_horizons || {};

    const headers = [
      "Generated At", "Location", "Latitude", "Longitude", "Temp (C)", "Weather", "Rainfall (mm)", "Flood Probability", "Flood Risk", "Recommended Action",
      "24h_Risk", "24h_Rain", "48h_Risk", "48h_Rain", "72h_Risk", "72h_Rain"
    ];

    const row = [
      new Date().toISOString(),
      name,
      selectedPoint.lat,
      selectedPoint.lon,
      selectedPoint.temp_c,
      selectedPoint.weather_summary,
      selectedPoint.predicted_rainfall_mm,
      selectedPoint.flood_probability,
      selectedPoint.flood_risk,
      selectedPoint.recommended_action || selectedPoint.prediction?.recommended_action || 'Monitor',
      horizons['24h']?.risk || 'N/A', horizons['24h']?.rainfall_mm || 0,
      horizons['48h']?.risk || 'N/A', horizons['48h']?.rainfall_mm || 0,
      horizons['72h']?.risk || 'N/A', horizons['72h']?.rainfall_mm || 0
    ];

    const csvContent = [
      "North Cyprus Flood Prediction",
      "Prediction Analysis Report",
      "",
      headers.join(","),
      row.join(",")
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `Flood_Data_${name.replace(/\W+/g, '_')}.csv`;
    link.click();
  };

  return (
    <div className="app-container">
      <Header />

      <div className="content">
        <Sidebar
          riskLocations={riskLocations}
          selectedPoint={selectedPoint}
          onSelectPoint={async (p) => {
            setSearchResult({ lat: p.lat, lon: p.lon, zoom: 15 }); // Fly to location (110% zoom) 

            // 1. Instant update with known grid data + loading flag
            setSelectedPoint({ ...p, isLoadingDetails: true });

            if (!p.forecast || p.model_used !== selectedModel) {
              try {
                const res = await fetch(`/api/predict-location?lat=${p.lat}&lon=${p.lon}&model=${selectedModel}`);
                if (res.ok) {
                  const fullData = await res.json();
                  setSelectedPoint({
                    ...p,
                    ...fullData,
                    model_used: selectedModel,
                    temp_c: Math.round(fullData.temp_c),
                    flood_risk: fullData.prediction.flood_risk,
                    isLoadingDetails: false
                  });
                }
              } catch (e) {
                console.error(e);
              }
            }
          }}
          formatLocationName={formatLocationName}
        />

        <main className="main">
          <StatsPanel selectedPoint={selectedPoint} />

          {/* Action Bar */}
          <div style={{ display: 'flex', gap: '10px', marginBottom: '20px', alignItems: 'center' }}>
            <div style={{ display: 'flex', gap: '8px', flex: 1, maxWidth: '400px' }}>
              <button
                onClick={downloadPDF}
                disabled={!selectedPoint}
                style={{
                  background: '#1a73e8',
                  cursor: selectedPoint ? 'pointer' : 'not-allowed',
                  padding: '10px',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  fontWeight: '600',
                  flex: 1,
                  height: '42px',
                  fontSize: '13px',
                  boxShadow: '0 1px 2px 0 rgba(60,64,67,.3)'
                }}
              >
                Export PDF
              </button>
              <button
                onClick={downloadCSV}
                disabled={!selectedPoint}
                style={{
                  background: '#1e8e3e',
                  cursor: selectedPoint ? 'pointer' : 'not-allowed',
                  padding: '10px',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  fontWeight: '600',
                  flex: 1,
                  height: '42px',
                  fontSize: '13px',
                  boxShadow: '0 1px 2px 0 rgba(60,64,67,.3)'
                }}
              >
                Export CSV
              </button>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#e8f0fe', padding: '0 15px', borderRadius: '6px', border: '1px solid #1a73e8', height: '42px' }}>
              <span style={{ fontSize: '13px', fontWeight: 'bold', color: '#1a73e8' }}>Active Model:</span>
              <select
                value={selectedModel}
                onChange={(e) => handleModelChange(e.target.value)}
                style={{
                  border: 'none',
                  background: 'transparent',
                  fontSize: '13px',
                  fontWeight: 'bold',
                  color: '#0b5ed7',
                  cursor: 'pointer',
                  outline: 'none'
                }}
              >
                <option value="rf">Random Forest (Balanced)</option>
                <option value="xgb">XGBoost (Aggressive)</option>
                <option value="hybrid">Hybrid Ensemble (Accurate)</option>
              </select>
            </div>

            <div className="search-bar" style={{ display: 'flex', gap: '5px', flex: 1, maxWidth: '400px' }}>
              <input
                type="text"
                placeholder="Search location (e.g. Kyrenia)"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  padding: '10px',
                  border: '1px solid #ccc',
                  borderRadius: '4px',
                  flex: 1,
                  height: '42px'
                }}
                onKeyDown={(e) => e.key === 'Enter' && searchLocation()}
              />
              <button
                onClick={searchLocation}
                style={{
                  background: '#0b5ed7',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  padding: '0 20px',
                  fontWeight: 'bold',
                  cursor: 'pointer',
                  height: '42px'
                }}
              >
                Search
              </button>
            </div>
          </div>

          <div className="map-wrapper" style={{ flex: 1, display: 'flex', minHeight: '500px' }}>
            <MapView
              onSelectPoint={(p) => {
                setSelectedPoint(p);
                setSearchResult(null); // Clear search marker when manually selecting or reloading
              }}
              selectedPoint={selectedPoint}
              flyToLocation={searchResult}
              grid={cleanGrid}
              status={status}
              loadGrid={loadGrid}
              refreshNow={refreshNow}
            />
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
