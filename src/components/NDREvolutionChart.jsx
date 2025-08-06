import React, { useState, useEffect } from 'react';

const BACKEND_URL = 'http://localhost:8000';

export default function NDREvolutionChart() {
  const [ndrData, setNdrData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchNDREvolution = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${BACKEND_URL}/ndr-evolution`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      if (data.error) {
        throw new Error(data.error);
      }
      
      setNdrData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNDREvolution();
  }, []);

  const renderChart = () => {
    if (!ndrData || !ndrData.ndr_evolution) return null;

    const evolution = ndrData.ndr_evolution;
    // Reverse the data to show M13 on the left and M24 on the right
    const reversedEvolution = [...evolution].reverse();
    const validData = reversedEvolution.filter(item => item.ndr_percentage !== null);
    
    if (validData.length === 0) return <p>No valid NDR data available</p>;

    const width = Math.max(800, validData.length * 40);
    const height = 400;
    const margin = { top: 20, right: 30, bottom: 40, left: 60 };
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;

    // Calculate scales
    const ndrValues = validData.map(d => d.ndr_percentage);
    const maxNDR = Math.max(...ndrValues);
    const minNDR = Math.min(...ndrValues);
    const yRange = maxNDR - minNDR;
    
    const xScale = (index) => margin.left + (index / (validData.length - 1)) * chartWidth;
    const yScale = (value) => margin.top + chartHeight - ((value - minNDR) / yRange) * chartHeight;

    // Create path for the line
    let pathData = '';
    validData.forEach((item, index) => {
      const x = xScale(index);
      const y = yScale(item.ndr_percentage);
      if (index === 0) {
        pathData += `M ${x} ${y}`;
      } else {
        pathData += ` L ${x} ${y}`;
      }
    });

    return (
      <div style={{ margin: '20px 0', padding: '20px', border: '1px solid #ddd', borderRadius: '8px', backgroundColor: '#fff' }}>
        <h3 style={{ marginTop: 0, marginBottom: '20px', color: '#333' }}>Full Base NDR Evolution</h3>
        
        <svg width={width} height={height} style={{ display: 'block', margin: '0 auto' }}>
          {/* Grid lines */}
          {[minNDR, (minNDR + maxNDR) / 2, maxNDR].map((tick, i) => (
            <g key={i}>
              <line 
                x1={margin.left} 
                x2={width - margin.right} 
                y1={yScale(tick)} 
                y2={yScale(tick)} 
                stroke="#eee" 
                strokeWidth="1"
              />
              <text 
                x={margin.left - 10} 
                y={yScale(tick) + 4} 
                fontSize="12" 
                fill="#666" 
                textAnchor="end"
              >
                {Math.round(tick)}%
              </text>
            </g>
          ))}
          
          {/* X-axis labels */}
          {validData.map((item, index) => (
            <text 
              key={index}
              x={xScale(index)} 
              y={height - 10} 
              fontSize="11" 
              fill="#666" 
              textAnchor="middle"
            >
              {item.month}
            </text>
          ))}
          
          {/* Y-axis label */}
          <text 
            x={-height/2} 
            y={20} 
            fontSize="14" 
            fill="#333" 
            textAnchor="middle" 
            transform={`rotate(-90 20,${height/2})`}
          >
            NDR (%)
          </text>
          
          {/* X-axis label */}
          <text 
            x={width/2} 
            y={height - 2} 
            fontSize="14" 
            fill="#333" 
            textAnchor="middle"
          >
            Month
          </text>
          
          {/* Line */}
          <path 
            d={pathData} 
            fill="none" 
            stroke="#1976d2" 
            strokeWidth="3"
          />
          
          {/* Data points */}
          {validData.map((item, index) => (
            <circle 
              key={index}
              cx={xScale(index)} 
              cy={yScale(item.ndr_percentage)} 
              r="4" 
              fill="#1976d2" 
              stroke="#fff" 
              strokeWidth="2"
            />
          ))}
        </svg>
      </div>
    );
  };

  if (loading) {
    return (
      <div style={{ margin: '20px 0', padding: '20px', border: '1px solid #ddd', borderRadius: '8px', textAlign: 'center' }}>
        <p>Loading NDR evolution data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ margin: '20px 0', padding: '20px', border: '1px solid #f5c6cb', borderRadius: '8px', backgroundColor: '#f8d7da', color: '#721c24' }}>
        <p><strong>Error loading NDR evolution data:</strong> {error}</p>
        <button 
          onClick={fetchNDREvolution}
          style={{
            padding: '8px 16px',
            backgroundColor: '#721c24',
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

  return renderChart();
} 