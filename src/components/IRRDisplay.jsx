import React, { useState, useEffect } from 'react';

export default function IRRDisplay() {
  const [irrData, setIrrData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasRunAnalysis, setHasRunAnalysis] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    // Check if Risk Analysis has been run by looking for transform results
    const checkAnalysisStatus = () => {
      const transformResults = localStorage.getItem('transformResults');
      console.log('Checking transform results:', transformResults);
      if (transformResults) {
        try {
          const results = JSON.parse(transformResults);
          console.log('Parsed results:', results);
          if (results && Object.keys(results).length > 0) {
            console.log('Setting hasRunAnalysis to true');
            setHasRunAnalysis(true);
            fetchIRRData();
          }
        } catch (e) {
          console.error('Error parsing transform results:', e);
        }
      }
    };

    checkAnalysisStatus();
    
    // Set up polling to check for transform results every 1 second
    const pollInterval = setInterval(() => {
      const transformResults = localStorage.getItem('transformResults');
      if (transformResults && !hasRunAnalysis) {
        try {
          const results = JSON.parse(transformResults);
          if (results && Object.keys(results).length > 0) {
            console.log('Polling detected transform results, setting hasRunAnalysis to true');
            setHasRunAnalysis(true);
            fetchIRRData();
            clearInterval(pollInterval);
          }
        } catch (e) {
          console.error('Error parsing transform results:', e);
        }
      }
    }, 1000);

    // Enhanced polling for when analysis has already been run
    const refreshInterval = setInterval(() => {
      if (hasRunAnalysis) {
        const transformResults = localStorage.getItem('transformResults');
        if (transformResults) {
          try {
            const results = JSON.parse(transformResults);
            // Check if the results have been updated (this is a simple check)
            const resultsString = JSON.stringify(results);
            if (resultsString !== lastUpdate) {
              console.log('Detected updated transform results, refreshing IRR data');
              setLastUpdate(resultsString);
              fetchIRRData();
            }
          } catch (e) {
            console.error('Error parsing transform results:', e);
          }
        }
      }
    }, 2000); // Check every 2 seconds for updates

    // Listen for changes to transform results
    const handleStorageChange = () => {
      console.log('Storage change detected');
      checkAnalysisStatus();
    };

    window.addEventListener('storage', handleStorageChange);
    
    return () => {
      window.removeEventListener('storage', handleStorageChange);
      clearInterval(pollInterval);
      clearInterval(refreshInterval);
    };
  }, [hasRunAnalysis, lastUpdate]);

  const fetchIRRData = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/get-irr-data', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setIrrData(data);
      console.log('IRR data refreshed:', data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    console.log('Refresh button clicked');
    fetchIRRData();
  };

  const handleRetry = () => {
    console.log('Retry button clicked');
    // Force check for transform results and reload IRR data
    const transformResults = localStorage.getItem('transformResults');
    console.log('Retry - transform results:', transformResults);
    if (transformResults) {
      try {
        const results = JSON.parse(transformResults);
        console.log('Retry - parsed results:', results);
        if (results && Object.keys(results).length > 0) {
          console.log('Retry - setting hasRunAnalysis to true');
          setHasRunAnalysis(true);
          fetchIRRData();
        } else {
          console.log('Retry - no valid results found');
        }
      } catch (e) {
        console.error('Error parsing transform results:', e);
      }
    } else {
      console.log('Retry - no transform results found in localStorage');
    }
  };

  const formatIRR = (irr) => {
    if (irr === null || irr === undefined) return 'N/A';
    return `${(irr * 100).toFixed(2)}%`;
  };

  const getIRRColor = (irr) => {
    if (irr === null || irr === undefined) return '#f3f3f3';
    if (irr >= 0.20) return '#eaf3ea'; // green for high IRR
    if (irr >= 0.10) return '#fffbe6'; // yellow for medium IRR
    if (irr >= 0) return '#fdeaea'; // red for low positive IRR
    return '#f3f3f3'; // grey for negative IRR
  };

  if (loading) {
    return (
      <div style={{ 
        margin: '32px 0', 
        padding: '20px', 
        textAlign: 'center',
        backgroundColor: '#f8f9fa',
        borderRadius: '8px',
        border: '1px solid #dee2e6'
      }}>
        <div>Loading IRR data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ 
        margin: '32px 0', 
        padding: '20px',
        backgroundColor: '#f8d7da',
        color: '#721c24',
        border: '1px solid #f5c6cb',
        borderRadius: '8px'
      }}>
        <div>Error loading IRR data: {error}</div>
        <button 
          onClick={fetchIRRData}
          style={{
            marginTop: '12px',
            padding: '8px 16px',
            backgroundColor: '#dc3545',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  if (!hasRunAnalysis) {
    return (
      <div style={{ 
        margin: '32px 0', 
        padding: '20px',
        backgroundColor: '#fff3cd',
        color: '#856404',
        border: '1px solid #ffeaa7',
        borderRadius: '8px'
      }}>
        <div style={{ marginBottom: '12px' }}>Please run the Risk Analysis first to see IRR data.</div>
        <button 
          onClick={handleRetry}
          style={{
            padding: '8px 16px',
            backgroundColor: '#856404',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '14px'
          }}
        >
          Retry
        </button>
        <div style={{ marginTop: '8px', fontSize: '12px', color: '#856404' }}>
          Debug: hasRunAnalysis = {hasRunAnalysis.toString()}
        </div>
      </div>
    );
  }

  if (!irrData || !irrData.files || irrData.files.length === 0) {
    return (
      <div style={{ 
        margin: '32px 0', 
        padding: '20px',
        backgroundColor: '#fff3cd',
        color: '#856404',
        border: '1px solid #ffeaa7',
        borderRadius: '8px'
      }}>
        <div style={{ marginBottom: '12px' }}>No IRR data available. Please run the Risk Analysis first.</div>
        <button 
          onClick={handleRetry}
          style={{
            padding: '8px 16px',
            backgroundColor: '#856404',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '14px'
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div style={{ margin: '32px 0' }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '18px'
      }}>
        <h2 style={{ color: '#1976d2', margin: 0 }}>5yr simulations average IRR on CAC</h2>
        <button 
          onClick={handleRefresh}
          style={{
            padding: '6px 12px',
            backgroundColor: '#1976d2',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '12px',
            display: 'flex',
            alignItems: 'center',
            gap: '4px'
          }}
        >
          🔄 Refresh
        </button>
      </div>
      
      <div style={{ 
        display: 'flex',
        justifyContent: 'center'
      }}>
        {irrData.files
          .filter(file => file.name.includes('less_conservative_'))
          .slice(0, 1)
          .map((file, index) => (
            <div key={index} style={{ 
              padding: '16px 24px',
              textAlign: 'center',
              fontFamily: 'monospace',
              fontWeight: '600',
              fontSize: '14px',
              backgroundColor: getIRRColor(file.irr),
              color: file.irr !== null && file.irr !== undefined ? 
                (file.irr >= 0.20 ? '#28a745' : file.irr >= 0.10 ? '#ffc107' : '#dc3545') : '#6c757d',
              borderRadius: '4px'
            }}>
              {formatIRR(file.irr)}
            </div>
          ))}
      </div>
    </div>
  );
} 