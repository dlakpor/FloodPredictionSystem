import React, { useState } from 'react';

export default function StatsPanel({ selectedPoint }) {
    if (!selectedPoint) {
        return (
            <div style={{ padding: '20px', border: '1px dashed #ccc', borderRadius: '8px', textAlign: 'center', color: '#666', marginBottom: '15px' }}>
                Select a location to view detailed weather and flood stats.
            </div>
        );
    }

    const [activeTab, setActiveTab] = useState('temp');
    const { forecast, temp_c, humidity, wind_kph, precipitation_prob, weather_summary, location_name, location } = selectedPoint;
    const displayName = location_name || location?.name || 'Selected Location';
    const isFetching = selectedPoint.flood_risk === "Loading..." || selectedPoint.isLoadingDetails;

    // Helper to get metric for graph
    const getGraphData = () => {
        if (!forecast?.hourly) return [];
        return forecast.hourly.map(h => ({
            time: h.time,
            val: activeTab === 'temp' ? h.temp : activeTab === 'precip' ? (h.precip || 0) : (h.wind || 0)
        }));
    };

    const graphData = getGraphData();
    const config = {
        temp: { color: '#fbbc04', unit: '°', max: 50 },
        precip: { color: '#4285f4', unit: '%', max: 100 },
        wind: { color: '#34a853', unit: ' km/h', max: 100 }
    }[activeTab];

    return (
        <div style={{ display: 'flex', flexDirection: 'row', gap: '15px', marginBottom: '15px', alignItems: 'stretch' }}>

            {/* GOOGLE STYLE WEATHER WIDGET */}
            <div style={{
                background: 'white',
                color: '#202124',
                borderRadius: '8px',
                padding: '16px 20px',
                fontFamily: 'Roboto, Arial, sans-serif',
                boxShadow: '0 1px 2px 0 rgba(60,64,67,.3), 0 1px 3px 1px rgba(60,64,67,.15)',
                border: '1px solid #dadce0',
                width: '450px',
                flexShrink: 0
            }}>
                {/* Search Results Label */}
                <div style={{ fontSize: '14px', color: '#70757a', marginBottom: '8px' }}>
                    Results for <span style={{ fontWeight: 'bold', color: '#202124' }}>{displayName}</span>
                </div>

                {/* Top Section */}
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                        <div style={{ fontSize: '42px', fontWeight: '400', color: '#202124' }}>
                            {!isFetching && temp_c !== undefined ? Math.round(temp_c) : <span style={{ fontSize: '20px', color: '#999' }}>...</span>}
                            <span style={{ fontSize: '18px', verticalAlign: 'top', marginLeft: '2px' }}>°C</span>
                        </div>
                        <div style={{ color: '#70757a', fontSize: '13px', lineHeight: '1.5' }}>
                            <div>Precipitation: <span style={{ color: '#202124' }}>{precipitation_prob ?? 0}%</span></div>
                            <div>Humidity: <span style={{ color: '#202124' }}>{humidity ?? '--'}%</span></div>
                            <div>Wind: <span style={{ color: '#202124' }}>{wind_kph ?? '--'} km/h</span></div>
                        </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: '18px', fontWeight: '400', color: '#202124' }}>Weather</div>
                        <div style={{ color: '#70757a', fontSize: '12px' }}>
                            {new Date().toLocaleDateString('en-US', { weekday: 'long', hour: 'numeric', minute: '2-digit' })}
                        </div>
                        <div style={{ textTransform: 'capitalize', fontWeight: '500', color: '#202124', marginTop: '2px', fontSize: '14px' }}>
                            {weather_summary || 'Loading status...'}
                        </div>
                    </div>
                </div>

                {/* Tabs - Minimal */}
                <div style={{ display: 'flex', gap: '20px', borderBottom: '1px solid #ebebeb', marginBottom: '12px', fontSize: '13px' }}>
                    <div
                        onClick={() => setActiveTab('temp')}
                        style={{
                            paddingBottom: '8px',
                            color: activeTab === 'temp' ? '#1a73e8' : '#70757a',
                            borderBottom: activeTab === 'temp' ? '2px solid #1a73e8' : 'none',
                            cursor: 'pointer',
                            fontWeight: activeTab === 'temp' ? '500' : '400'
                        }}>Temperature</div>
                    <div
                        onClick={() => setActiveTab('precip')}
                        style={{
                            paddingBottom: '8px',
                            color: activeTab === 'precip' ? '#1a73e8' : '#70757a',
                            borderBottom: activeTab === 'precip' ? '2px solid #1a73e8' : 'none',
                            cursor: 'pointer',
                            fontWeight: activeTab === 'precip' ? '500' : '400'
                        }}>Precipitation</div>
                    <div
                        onClick={() => setActiveTab('wind')}
                        style={{
                            paddingBottom: '8px',
                            color: activeTab === 'wind' ? '#1a73e8' : '#70757a',
                            borderBottom: activeTab === 'wind' ? '2px solid #1a73e8' : 'none',
                            cursor: 'pointer',
                            fontWeight: activeTab === 'wind' ? '500' : '400'
                        }}>Wind</div>
                </div>

                {/* Graph Area - Tighter */}
                <div style={{ height: '50px', position: 'relative', marginBottom: '8px' }}>
                    {graphData.length > 0 ? (
                        <svg width="100%" height="100%" viewBox={`0 0 ${graphData.length * 100} 100`} preserveAspectRatio="none">
                            <path
                                d={`M 0 50 ${graphData.map((h, i) => `L ${i * 100} ${80 - (h.val * (80 / config.max))}`).join(' ')}`}
                                fill="none"
                                stroke={config.color}
                                strokeWidth="3"
                            />
                            {graphData.map((h, i) => (
                                <text key={i} x={i * 100} y={80 - (h.val * (80 / config.max)) - 15} fill="#202124" fontSize="16" fontWeight="500" textAnchor="middle">{h.val}{config.unit}</text>
                            ))}
                        </svg>
                    ) : (
                        <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#70757a', fontSize: '12px' }}>
                            {isFetching ? 'Fetching live forecast...' : 'Loading hourly data...'}
                        </div>
                    )}
                </div>

                {/* Hourly Times */}
                <div style={{ display: 'flex', justifyContent: 'space-between', color: '#70757a', fontSize: '11px', marginBottom: '15px' }}>
                    {forecast?.hourly?.map((h, i) => (
                        <div key={i}>{h.time}</div>
                    ))}
                </div>

                {/* Daily Forecast Row - Compact */}
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: '3px', overflowX: 'auto' }}>
                    {forecast?.daily?.map((d, i) => (
                        <div key={i} style={{
                            flex: 1,
                            minWidth: '40px',
                            background: i === 0 ? '#f1f3f4' : 'transparent',
                            padding: '6px 2px',
                            borderRadius: '4px',
                            textAlign: 'center',
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            gap: '3px'
                        }}>
                            <div style={{ fontSize: '10px', fontWeight: '500' }}>{d.day}</div>
                            <div style={{ fontSize: '14px' }}>{getWeatherEmoji(d.icon)}</div>
                            <div style={{ fontSize: '10px' }}>
                                <span style={{ fontWeight: '500' }}>{d.high}°</span>
                                <span style={{ color: '#70757a', marginLeft: '2px' }}>{d.low}°</span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* FLOOD SPECIFIC STATS - SIDE BY SIDE NEXT TO WIDGET */}
            <div style={{ display: 'flex', flexDirection: 'row', gap: '12px', flex: 1 }}>
                <StatsCard
                    title="Flood Assessment"
                    value={
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            {/* CAUSE: Rainfall + Explanation */}
                            <div>
                                <div style={{ fontSize: '13px', color: '#5f6368', fontWeight: '500' }}>Expected Rainfall</div>
                                <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#202124', margin: '3px 0' }}>
                                    {(selectedPoint.predicted_rainfall_mm || 0).toFixed(2)} mm
                                </div>
                                <div style={{ fontSize: '11px', color: '#70757a', lineHeight: '1.4', fontStyle: 'italic' }}>
                                    Influenced by moisture and topography.
                                </div>
                            </div>

                            {/* DIVIDER */}
                            <div style={{ borderTop: '1px solid #ebebeb' }}></div>

                            {/* EFFECT: Final Probability */}
                            <div>
                                <div style={{ fontSize: '13px', color: '#5f6368', fontWeight: '500' }}>Flood Probability</div>
                                <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#202124', marginTop: '4px' }}>
                                    {(Number(selectedPoint.flood_probability) * 100).toFixed(1)}%
                                </div>
                            </div>
                        </div>
                    }
                    color={Number(selectedPoint.flood_probability) > 0.3 ? '#d93025' : Number(selectedPoint.flood_probability) > 0.1 ? '#f9ab00' : '#1e8e3e'}
                />
                <StatsCard
                    title="Flood Risk & Action"
                    value={
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                            <div>
                                <div style={{ fontSize: '13px', color: '#5f6368', fontWeight: '500' }}>Current Risk Level</div>
                                <div style={{ fontWeight: 'bold', fontSize: '20px', color: selectedPoint.flood_risk === "High" ? '#d93025' : selectedPoint.flood_risk === "Moderate" ? '#f9ab00' : '#1e8e3e' }}>
                                    {selectedPoint.flood_risk}
                                </div>
                            </div>

                            <div style={{ borderTop: '1px solid #ebebeb', margin: '3px 0' }}></div>

                            <div>
                                <div style={{ fontSize: '13px', color: '#5f6368', fontWeight: '500' }}>Safety Protocol</div>
                                <div style={{ fontSize: '14px', fontWeight: 'bold', color: '#202124', margin: '2px 0' }}>
                                    Action: {selectedPoint.recommended_action || selectedPoint.prediction?.recommended_action || "Monitor"}
                                </div>
                                <div style={{ fontSize: '11px', color: '#70757a', lineHeight: '1.4', fontStyle: 'italic', marginTop: '3px' }}>
                                    {selectedPoint.flood_risk === "High" ?
                                        "Activate emergency plans immediately." :
                                        selectedPoint.flood_risk === "Moderate" ?
                                            "Secure property & monitor drainage." :
                                            "Conditions stable. Monitor updates."
                                    }
                                </div>
                            </div>
                        </div>
                    }
                    color={selectedPoint.flood_risk === "High" ? '#d93025' : selectedPoint.flood_risk === "Moderate" ? '#f9ab00' : '#1e8e3e'}
                />

                {/* FUTURE OUTLOOK CARD */}
                <StatsCard
                    title="Future Outlook"
                    value={
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            {['24h', '48h', '72h'].map((horizon) => {
                                const data = selectedPoint.prediction?.future_horizons?.[horizon];
                                if (!data) return null;
                                return (
                                    <div key={horizon} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px', background: '#f8f9fa', padding: '5px 8px', borderRadius: '4px' }}>
                                        <div style={{ fontWeight: 'bold' }}>{horizon} ({data.time.split(' ')[0]})</div>
                                        <div style={{ color: data.risk === 'High' ? '#d93025' : data.risk === 'Moderate' ? '#f9ab00' : '#1e8e3e', fontWeight: 'bold' }}>
                                            {data.risk}
                                        </div>
                                        <div style={{ color: '#666' }}>{data.rainfall_mm}mm</div>
                                    </div>
                                );
                            })}
                            {!selectedPoint.prediction?.future_horizons && (
                                <div style={{ fontSize: '11px', color: '#999', fontStyle: 'italic' }}>
                                    Future predictions updating...
                                </div>
                            )}
                        </div>
                    }
                    color="#4285f4"
                />
            </div>
        </div>
    );
}

function getWeatherEmoji(main) {
    const map = {
        'Clear': '☀️',
        'Clouds': '☁️',
        'Rain': '🌧️',
        'Drizzle': '🌦️',
        'Thunderstorm': '⛈️',
        'Snow': '❄️',
        'Mist': '🌫️',
        'Fog': '🌫️',
        'Haze': '🌫️'
    };
    return map[main] || '☀️';
}

function StatsCard({ title, value, color }) {
    return (
        <div style={{
            background: 'white',
            padding: '20px',
            borderRadius: '8px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)',
            border: '1px solid #dadce0',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            flex: 1,
            minWidth: '150px'
        }}>
            <h3 style={{ margin: '0 0 8px 0', fontSize: '14px', color: '#000', fontWeight: 'bold' }}>{title}</h3>
            <div style={{ fontSize: '16px', color: '#202124' }}>{value}</div>
            <div style={{
                height: '4px',
                width: '40px',
                background: color,
                marginTop: '8px',
                borderRadius: '2px'
            }}></div>
        </div>
    );
}
