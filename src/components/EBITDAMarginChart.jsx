import React, { useState, useEffect } from 'react';

export default function EBITDAMarginChart() {
  const [marginData, setMarginData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const calculateEBITDAMargin = () => {
    setLoading(true);
    setError(null);
    
    try {
      // Get P&L data from localStorage
      const plDataRaw = localStorage.getItem('plData');
      console.log('Raw P&L data from localStorage:', plDataRaw);
      
      if (!plDataRaw) {
        throw new Error('No P&L data available');
      }
      
      const plData = JSON.parse(plDataRaw);
      console.log('Parsed P&L data:', plData);
      console.log('P&L data length:', plData?.length);
      console.log('First row sample:', plData?.[0]);
      
      if (!Array.isArray(plData) || plData.length === 0) {
        throw new Error('Invalid P&L data format');
      }
      
      // Calculate EBITDA excluding S&M margin for each month
      const marginEvolution = plData.map((row, index) => {
        console.log(`Processing row ${index}:`, row);
        
        const revenue = parseFloat(row.revenue) || 0;
        const ebitda = parseFloat(row.ebitda) || 0;
        const sm = parseFloat(row.sm) || 0;
        
        console.log(`Row ${index} values - Revenue: ${revenue}, EBITDA: ${ebitda}, S&M: ${sm}`);
        
        if (revenue === 0) {
          console.log(`Row ${index} has zero revenue, skipping`);
          return {
            month: row.month,
            margin_percentage: null
          };
        }
        
        // Calculate (EBITDA + S&M) / Revenue
        const ebitdaExcludingSM = ebitda + sm;
        const marginPercentage = (ebitdaExcludingSM / revenue) * 100;
        
        console.log(`Row ${index} calculation - EBITDA+S&M: ${ebitdaExcludingSM}, Margin: ${marginPercentage}%`);
        
        // Abbreviate month name
        const monthName = row.month;
        let abbreviatedMonth = monthName;
        
        // Extract month and year, then abbreviate
        if (monthName.includes(' ')) {
          const parts = monthName.split(' ');
          if (parts.length >= 2) {
            const month = parts[0].substring(0, 3);
            const year = parts[1].substring(2); // Get last 2 digits of year
            abbreviatedMonth = `${month}'${year}`;
          }
        }
        
        return {
          month: abbreviatedMonth,
          margin_percentage: marginPercentage
        };
      });
      
      console.log('Final margin evolution:', marginEvolution);
      const validData = marginEvolution.filter(item => item.margin_percentage !== null);
      console.log('Valid data count:', validData.length);
      
      setMarginData({ margin_evolution: marginEvolution });
    } catch (err) {
      console.error('Error in calculateEBITDAMargin:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    calculateEBITDAMargin();
    
    // Set up polling to check for P&L data updates every 2 seconds
    const pollInterval = setInterval(() => {
      const plDataRaw = localStorage.getItem('plData');
      if (plDataRaw) {
        try {
          const plData = JSON.parse(plDataRaw);
          if (Array.isArray(plData) && plData.length > 0) {
            // Check if we have valid data with revenue
            const hasValidData = plData.some(row => {
              const revenue = parseFloat(row.revenue) || 0;
              return revenue > 0;
            });
            
            if (hasValidData && (!marginData || marginData.margin_evolution.length === 0)) {
              console.log('Detected new P&L data, recalculating EBITDA margin');
              calculateEBITDAMargin();
            }
          }
        } catch (e) {
          console.error('Error checking P&L data:', e);
        }
      }
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [marginData]);

  const handleRetry = () => {
    console.log('Retry button clicked for EBITDA margin chart');
    calculateEBITDAMargin();
  };

  const renderChart = () => {
    if (!marginData || !marginData.margin_evolution) return null;

    const evolution = marginData.margin_evolution;
    const validData = evolution.filter(item => item.margin_percentage !== null);
    
    if (validData.length === 0) {
      return (
        <div style={{ 
          margin: '20px 0', 
          padding: '20px', 
          border: '1px solid #ffeaa7', 
          borderRadius: '8px', 
          backgroundColor: '#fff3cd',
          color: '#856404',
          textAlign: 'center'
        }}>
          <p style={{ marginBottom: '12px' }}>No valid EBITDA margin data available</p>
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

    const width = Math.max(800, validData.length * 40);
    const height = 400;
    const margin = { top: 20, right: 30, bottom: 40, left: 60 };
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;

    // Calculate scales
    const marginValues = validData.map(d => d.margin_percentage);
    const maxMargin = Math.max(...marginValues);
    const minMargin = Math.min(...marginValues);
    const yRange = maxMargin - minMargin;
    
    const xScale = (index) => margin.left + (index / (validData.length - 1)) * chartWidth;
    const yScale = (value) => margin.top + chartHeight - ((value - minMargin) / yRange) * chartHeight;

    // Create path for the line
    let pathData = '';
    validData.forEach((item, index) => {
      const x = xScale(index);
      const y = yScale(item.margin_percentage);
      if (index === 0) {
        pathData += `M ${x} ${y}`;
      } else {
        pathData += ` L ${x} ${y}`;
      }
    });

    return (
      <div style={{ margin: '20px 0', padding: '20px', border: '1px solid #ddd', borderRadius: '8px', backgroundColor: '#fff' }}>
        <h3 style={{ marginTop: 0, marginBottom: '20px', color: '#333' }}>EBITDA Excluding S&M Margin</h3>
        
        <svg width={width} height={height} style={{ display: 'block', margin: '0 auto' }}>
          {/* Grid lines */}
          {[minMargin, (minMargin + maxMargin) / 2, maxMargin].map((tick, i) => (
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
          
          {/* X-axis labels - show only every other month */}
          {validData.map((item, index) => {
            if (index % 2 === 0) {
              return (
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
              );
            }
            return null;
          })}
          
          {/* Y-axis label */}
          <text 
            x={-height/2} 
            y={20} 
            fontSize="14" 
            fill="#333" 
            textAnchor="middle" 
            transform={`rotate(-90 20,${height/2})`}
          >
            EBITDA Margin (%)
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
            stroke="#43a047" 
            strokeWidth="3"
          />
          
          {/* Data points */}
          {validData.map((item, index) => (
            <circle 
              key={index}
              cx={xScale(index)} 
              cy={yScale(item.margin_percentage)} 
              r="4" 
              fill="#43a047" 
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
        <p>Loading EBITDA margin data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ margin: '20px 0', padding: '20px', border: '1px solid #f5c6cb', borderRadius: '8px', backgroundColor: '#f8d7da', color: '#721c24' }}>
        <p><strong>Error loading EBITDA margin data:</strong> {error}</p>
        <button 
          onClick={handleRetry}
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