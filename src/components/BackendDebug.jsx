import React, { useState } from 'react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

export default function BackendDebug() {
  const [healthStatus, setHealthStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const checkBackendHealth = async () => {
    setLoading(true);
    setError(null);
    setHealthStatus(null);

    try {
      console.log('Checking backend health at:', `${BACKEND_URL}/health`);
      
      const response = await fetch(`${BACKEND_URL}/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      console.log('Health check response status:', response.status);
      console.log('Health check response headers:', response.headers);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Health check failed: ${response.status} - ${errorText}`);
      }

      const result = await response.json();
      console.log('Health check result:', result);
      
      setHealthStatus({
        success: true,
        status: result.status,
        backendUrl: BACKEND_URL
      });
    } catch (err) {
      console.error('Health check error:', err);
      setError(`Health check failed: ${err.message}. Backend URL: ${BACKEND_URL}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ 
      border: '1px solid #ddd', 
      padding: '20px', 
      borderRadius: '8px', 
      margin: '20px 0',
      backgroundColor: '#f9f9f9'
    }}>
      <h3>🔧 Backend Connection Debug</h3>
      <p><strong>Backend URL:</strong> {BACKEND_URL}</p>
      
      <button 
        onClick={checkBackendHealth}
        disabled={loading}
        style={{
          padding: '10px 20px',
          backgroundColor: '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: loading ? 'not-allowed' : 'pointer',
          opacity: loading ? 0.6 : 1
        }}
      >
        {loading ? 'Checking...' : 'Test Backend Connection'}
      </button>

      {healthStatus && (
        <div style={{ 
          marginTop: '15px', 
          padding: '10px', 
          backgroundColor: '#d4edda', 
          border: '1px solid #c3e6cb',
          borderRadius: '4px',
          color: '#155724'
        }}>
          <strong>✅ Backend is healthy!</strong>
          <br />
          Status: {healthStatus.status}
          <br />
          URL: {healthStatus.backendUrl}
        </div>
      )}

      {error && (
        <div style={{ 
          marginTop: '15px', 
          padding: '10px', 
          backgroundColor: '#f8d7da', 
          border: '1px solid #f5c6cb',
          borderRadius: '4px',
          color: '#721c24'
        }}>
          <strong>❌ Connection failed:</strong>
          <br />
          {error}
        </div>
      )}

      <div style={{ marginTop: '15px', fontSize: '14px', color: '#666' }}>
        <strong>Troubleshooting tips:</strong>
        <ul>
          <li>Make sure your backend is deployed and running</li>
          <li>Check that the VITE_BACKEND_URL environment variable is set correctly</li>
          <li>Verify the backend URL is accessible in your browser</li>
          <li>Check the browser's developer console for more detailed error messages</li>
        </ul>
      </div>
    </div>
  );
} 