import React from 'react';

export default function Sidebar({ riskLocations, selectedPoint, onSelectPoint, formatLocationName }) {
    return (
        <aside className="sidebar" style={{
            width: '210px',
            background: 'white',
            padding: '15px',
            borderRight: '1px solid #dee2e6',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            zIndex: 10
        }}>
            <h3 style={{ margin: '0 0 12px 0', fontSize: '15px', fontWeight: 'bold' }}>Controls</h3>
            <hr style={{ border: '0', borderTop: '1px solid #eee', marginBottom: '15px' }} />

            <h4 style={{ margin: '0 0 8px 0', fontSize: '12px', color: '#1a1a1a', fontWeight: 'bold' }}>Predictions (High to Low)</h4>

            <div style={{ flex: 1, overflowY: 'auto' }}>
                {riskLocations.length === 0 && (
                    <div style={{ fontSize: '11px', color: '#666', fontStyle: 'italic' }}>
                        Waiting for prediction data...
                    </div>
                )}

                {riskLocations.map((p, i) => (
                    <div
                        key={i}
                        onClick={() => onSelectPoint(p)}
                        style={{
                            padding: '9px',
                            marginBottom: '8px',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            background: (selectedPoint && selectedPoint.lat === p.lat && selectedPoint.lon === p.lon) ? '#e7f1ff' : 'white',
                            border: '1px solid #dee2e6',
                            borderLeft: `4px solid ${p.flood_risk === "High" ? "#dc3545" :
                                p.flood_risk === "Moderate" ? "#ffc107" : "#198754"
                                }`,
                            transition: 'background 0.2s',
                            boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
                        }}
                    >
                        <div style={{ fontWeight: 'bold', fontSize: '11px', marginBottom: '3px', color: '#333' }}>
                            Location: {formatLocationName ? formatLocationName(p) : `Loc: ${p.lat.toFixed(2)}, ${p.lon.toFixed(2)}`}
                        </div>
                        <div style={{ fontSize: '10px', color: '#555', marginBottom: '2px' }}>
                            Grid: {p.lat.toFixed(4)}, {p.lon.toFixed(4)}
                        </div>
                        <div style={{ fontSize: '10px', color: '#444', marginBottom: '2px' }}>
                            {p.flood_risk} Risk
                        </div>
                        <div style={{ fontSize: '10px', color: '#666' }}>
                            Rain: {Number(p.predicted_rainfall_mm).toFixed(2)}mm
                        </div>
                        <div style={{ fontSize: '10px', fontWeight: 'bold', color: p.flood_risk === "High" ? "#dc3545" : p.flood_risk === "Moderate" ? "#ca8a04" : "#198754", marginTop: '3px' }}>
                            Action: {p.recommended_action || (p.prediction?.recommended_action) || "Monitor"}
                        </div>
                    </div>
                ))}
            </div>

            <div style={{ marginTop: 'auto', paddingTop: '15px', fontSize: '11px', color: '#999', borderTop: '1px solid #eee' }}>
                Predictions are grid-based and auto-generated.
            </div>
        </aside>
    );
}
