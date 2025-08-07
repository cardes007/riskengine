import React, { useState, useEffect } from 'react';
import config from '../config';

const BACKEND_URL = config.getBackendUrl();

export default function BackendDebug() {
  const [backendStatus, setBackendStatus] = useState('checking');
  const [error, setError] = useState(null);
  const [configInfo, setConfigInfo] = useState(null);

  useEffect(() => {
    checkBackendStatus();
    setConfigInfo({
      environment: config.getEnvironment(),
      backendUrl: config.getBackendUrl(),
      isConfigured: config.isBackendConfigured(),
      isDev: config.IS_DEV,
      isProd: config.IS_PROD
    });
  }, []);

  const checkBackendStatus = async () => {
    try {
      setBackendStatus('checking');
      setError(null);
      
      const response = await fetch(`${BACKEND_URL}/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        setBackendStatus('connected');
      } else {
        setBackendStatus('error');
        setError(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (err) {
      setBackendStatus('error');
      setError(err.message);
    }
  };

  const testImportEndpoint = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/test-import`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ test: true }),
      });

      if (response.ok) {
        alert('✅ Import endpoint is working!');
      } else {
        alert(`❌ Import endpoint error: ${response.status}`);
      }
    } catch (err) {
      alert(`❌ Import endpoint error: ${err.message}`);
    }
  };

  const getStatusColor = () => {
    switch (backendStatus) {
      case 'connected': return '#28a745';
      case 'error': return '#dc3545';
      case 'checking': return '#ffc107';
      default: return '#6c757d';
    }
  };

  const getStatusText = () => {
    switch (backendStatus) {
      case 'connected': return '✅ Connected';
      case 'error': return '❌ Error';
      case 'checking': return '⏳ Checking...';
      default: return '❓ Unknown';
    }
  };

  return (
    <div style={{ 
      margin: '20px 0', 
      padding: '20px', 
      border: '1px solid #ddd', 
      borderRadius: '8px',
      backgroundColor: '#f8f9fa'
    }}>
      <h3 style={{ marginTop: 0, color: '#495057' }}>🔧 Backend Debug Information</h3>
      
      <div style={{ marginBottom: '15px' }}>
        <strong>Environment:</strong> {configInfo?.environment || 'Loading...'}
      </div>
      
      <div style={{ marginBottom: '15px' }}>
        <strong>Backend URL:</strong> {configInfo?.backendUrl || 'Loading...'}
      </div>
      
      <div style={{ marginBottom: '15px' }}>
        <strong>Configuration Status:</strong> 
        <span style={{ 
          color: configInfo?.isConfigured ? '#28a745' : '#dc3545',
          marginLeft: '8px'
        }}>
          {configInfo?.isConfigured ? '✅ Configured' : '❌ Not Configured'}
        </span>
      </div>
      
      <div style={{ marginBottom: '15px' }}>
        <strong>Backend Status:</strong> 
        <span style={{ 
          color: getStatusColor(),
          marginLeft: '8px'
        }}>
          {getStatusText()}
        </span>
      </div>
      
      {error && (
        <div style={{ 
          marginBottom: '15px',
          padding: '10px',
          backgroundColor: '#f8d7da',
          border: '1px solid #f5c6cb',
          borderRadius: '4px',
          color: '#721c24'
        }}>
          <strong>Error:</strong> {error}
        </div>
      )}
      
      <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
        <button 
          onClick={checkBackendStatus}
          style={{
            padding: '8px 16px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          🔄 Retry Connection
        </button>
        
        <button 
          onClick={testImportEndpoint}
          style={{
            padding: '8px 16px',
            backgroundColor: '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          🧪 Test Import Endpoint
        </button>
      </div>
      
      {!configInfo?.isConfigured && (
        <div style={{ 
          marginTop: '15px',
          padding: '15px',
          backgroundColor: '#fff3cd',
          border: '1px solid #ffeaa7',
          borderRadius: '4px',
          color: '#856404'
        }}>
          <strong>⚠️ Configuration Issue Detected</strong>
          <p style={{ margin: '8px 0 0 0' }}>
            The backend URL is not properly configured. This will cause the "Import Data" button to fail in production.
          </p>
          <p style={{ margin: '8px 0 0 0' }}>
            <strong>To fix this:</strong>
          </p>
          <ul style={{ margin: '8px 0 0 0', paddingLeft: '20px' }}>
            <li>Check that the VITE_BACKEND_URL environment variable is set correctly</li>
            <li>Ensure your backend is deployed and accessible</li>
            <li>Verify CORS settings on your backend</li>
            <li>Check the network tab in browser dev tools for specific errors</li>
          </ul>
        </div>
      )}
    </div>
  );
} 