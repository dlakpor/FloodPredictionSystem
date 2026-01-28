import React from 'react';

export default function Header() {
    return (
        <header style={{
            background: '#0b5ed7',
            color: 'white',
            padding: '12px 20px',
            fontSize: '20px',
            fontWeight: 'bold',
            display: 'flex',
            alignItems: 'center',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            zIndex: 1000
        }}>
            <div>North Cyprus Flood Prediction System</div>
        </header>
    );
}
