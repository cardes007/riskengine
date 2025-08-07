import React, { useState } from 'react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

export default function BackendIntegration({ plData, cohortData }) {
  const [importResult, setImportResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [transformResult, setTransformResult] = useState(null);
  const [transformLoading, setTransformLoading] = useState(false);
  const [transformError, setTransformError] = useState(null);
  const [yearlyInterestRate, setYearlyInterestRate] = useState(16);
  const [interestRateInput, setInterestRateInput] = useState('16');

  const importAllData = async () => {
    setLoading(true);
    setError(null);
    setImportResult(null);

    // Load data directly from localStorage to ensure we get the most current data
    let currentPLData = [];
    let currentCohortData = [];
    
    try {
      const plDataRaw = localStorage.getItem('plData');
      const cohortDataRaw = localStorage.getItem('cohortData');
      
      if (plDataRaw) {
        currentPLData = JSON.parse(plDataRaw);
      }
      if (cohortDataRaw) {
        currentCohortData = JSON.parse(cohortDataRaw);
      }
      
      console.log('P&L Data loaded from localStorage:', currentPLData);
      console.log('P&L Data length:', currentPLData?.length);
      console.log('P&L Data type:', typeof currentPLData);
      console.log('P&L Data is array:', Array.isArray(currentPLData));
      console.log('Cohort Data loaded from localStorage:', currentCohortData);
      console.log('Cohort Data length:', currentCohortData?.length);
    } catch (error) {
      console.error('Error loading data from localStorage:', error);
      setError('Error loading data from localStorage: ' + error.message);
      setLoading(false);
      return;
    }

    try {
      console.log('Attempting to fetch from:', `${BACKEND_URL}/import/all`);
      console.log('Request payload:', {
        pl_data: currentPLData,
        cohort_data: currentCohortData
      });
      
      // Import all data in a single call
      const response = await fetch(`${BACKEND_URL}/import/all`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          pl_data: currentPLData,
          cohort_data: currentCohortData
        }),
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', response.headers);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Response error text:', errorText);
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
      }

      const result = await response.json();
      console.log('Response result:', result);

      setImportResult({
        success: true,
        sm_count: result.sm_data?.count || 0,
        cohort_count: result.cohort_data?.count || 0,
        full_cohorts_count: result.pl_data?.count || 0
      });
    } catch (err) {
      console.error('Import error details:', err);
      setError(`Import failed: ${err.message}. Backend URL: ${BACKEND_URL}`);
    } finally {
      setLoading(false);
    }
  };

  const runLenderCashflowTransform = async () => {
    setTransformLoading(true);
    setTransformError(null);
    setTransformResult(null);

    try {
      const response = await fetch(`${BACKEND_URL}/transform-to-lender-cashflows`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          yearly_interest_rate: yearlyInterestRate / 100 // Convert percentage to decimal
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      console.log('Debug: Transform result received:', result);
      console.log('Debug: Results data:', result.results);
      setTransformResult({
        success: true,
        message: result.message,
        files_created: result.files_created,
        results: result.results
      });
      
      // Save transform results to localStorage so IRRDisplay can detect when analysis is complete
      localStorage.setItem('transformResults', JSON.stringify(result.results));
    } catch (err) {
      setTransformError(err.message);
    } finally {
      setTransformLoading(false);
    }
  };


  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const getScenarioDisplayName = (scenarioKey) => {
    const scenarioMap = {
      'less_conservative_original': 'Monthly Less Conservative',
      'conservative_original': 'Monthly Conservative',
      'conservative_aggregated': 'Quarterly Conservative',
      'less_conservative_aggregated': 'Quarterly Less Conservative'
    };
    return scenarioMap[scenarioKey] || scenarioKey.replace('_', ' ');
  };

  return (
    <div style={{ margin: '24px 0' }}>
              <h2>Simulations & Risk Analysis</h2>
      
      
      <div style={{ display: 'flex', gap: '12px', marginBottom: '20px', flexWrap: 'wrap', justifyContent: 'center', alignItems: 'center' }}>
        <button 
          onClick={importAllData}
          disabled={loading}
          style={{
            padding: '12px 24px',
            backgroundColor: '#6f42c1',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.6 : 1,
            fontSize: '16px',
            fontWeight: '500'
          }}
        >
          {loading ? 'Importing...' : 'Import Data'}
        </button>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <label style={{ fontSize: '14px', fontWeight: '500', color: '#495057' }}>
            Yearly Interest Rate (%):
          </label>
          <input
            type="number"
            value={interestRateInput}
            onChange={(e) => {
              const value = e.target.value;
              setInterestRateInput(value);
              
              const numValue = parseFloat(value);
              if (!isNaN(numValue) && numValue >= 0 && numValue <= 100) {
                setYearlyInterestRate(numValue);
              }
            }}
            onBlur={(e) => {
              const value = e.target.value;
              const numValue = parseFloat(value);
              
              if (value === '' || isNaN(numValue) || numValue < 0 || numValue > 100) {
                setInterestRateInput('16');
                setYearlyInterestRate(16);
              } else {
                setInterestRateInput(numValue.toString());
                setYearlyInterestRate(numValue);
              }
            }}
            min="0"
            max="100"
            step="0.1"
            style={{
              padding: '8px 12px',
              border: '1px solid #ced4da',
              borderRadius: '4px',
              fontSize: '14px',
              width: '80px',
              textAlign: 'center'
            }}
          />
        </div>
        
        <button 
          onClick={runLenderCashflowTransform}
          disabled={transformLoading || !importResult?.success}
          style={{
            padding: '12px 24px',
            backgroundColor: '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: (transformLoading || !importResult?.success) ? 'not-allowed' : 'pointer',
            opacity: (transformLoading || !importResult?.success) ? 0.6 : 1,
            fontSize: '16px',
            fontWeight: '500'
          }}
        >
          {transformLoading ? 'Transforming...' : 'Run Risk Analysis'}
        </button>
      </div>

      {error && (
        <div style={{ 
          padding: '12px', 
          backgroundColor: '#f8d7da', 
          color: '#721c24', 
          border: '1px solid #f5c6cb', 
          borderRadius: '4px',
          marginBottom: '16px'
        }}>
          Error: {error}
        </div>
      )}

      {importResult && (
        <div style={{ 
          padding: '16px', 
          backgroundColor: '#d4edda', 
          border: '1px solid #c3e6cb', 
          borderRadius: '4px' 
        }}>
          <h3 style={{ marginTop: 0, color: '#155724' }}>Import Results</h3>
          
          {importResult.success && (
            <div style={{ marginBottom: '16px' }}>
              <p>Data imported successfully!</p>
              <p>P&L Data: {importResult.sm_count} records</p>
              <p>Full Cohorts: {importResult.full_cohorts_count} records</p>
            </div>
          )}
        </div>
      )}

      {transformError && (
        <div style={{ 
          padding: '12px', 
          backgroundColor: '#f8d7da', 
          color: '#721c24', 
          border: '1px solid #f5c6cb', 
          borderRadius: '4px',
          marginBottom: '16px'
        }}>
          Transform Error: {transformError}
        </div>
      )}

      {transformResult && (
        <div style={{ 
          padding: '16px', 
          backgroundColor: '#d1ecf1', 
          border: '1px solid #bee5eb', 
          borderRadius: '4px' 
        }}>
          <h3 style={{ marginTop: 0, color: '#0c5460' }}>Transform Results</h3>
          
          {transformResult.success && (
            <div style={{ marginBottom: '16px' }}>
              <p>{transformResult.message}</p>
              <p><strong>Files created:</strong> {transformResult.files_created}</p>
            </div>
          )}
        </div>
      )}

      {/* Lender Cashflow Summary Table */}
      {transformResult?.results && (
        <div style={{ 
          marginTop: '20px'
        }}>
          <h3 style={{ marginTop: 0, color: '#495057', marginBottom: '16px' }}>
            Lender Cashflow Summary
          </h3>
          
          <table style={{ 
            width: '100%', 
            borderCollapse: 'collapse',
            backgroundColor: 'white',
            borderRadius: '4px',
            overflow: 'hidden',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}>
            <thead>
              <tr style={{ backgroundColor: '#6c757d', color: 'white' }}>
                <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #dee2e6' }}>
                  Scenario
                </th>
                <th style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #dee2e6' }}>
                  Total Loan Amount
                </th>
                <th style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #dee2e6' }}>
                  Total Net Return
                </th>
                <th style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #dee2e6' }}>
                  Positive Return Rate
                </th>
                <th style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #dee2e6' }}>
                  IRR
                </th>
                <th style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #dee2e6' }}>
                  0-10% Loss
                </th>
                <th style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #dee2e6' }}>
                  10-20% Loss
                </th>
                <th style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #dee2e6' }}>
                  20-30% Loss
                </th>
                <th style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #dee2e6' }}>
                  30-40% Loss
                </th>
                <th style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #dee2e6' }}>
                  40-50% Loss
                </th>
                <th style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #dee2e6' }}>
                  50-60% Loss
                </th>
                <th style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #dee2e6' }}>
                  60-70% Loss
                </th>
                <th style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #dee2e6' }}>
                  70-80% Loss
                </th>
                <th style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #dee2e6' }}>
                  80-90% Loss
                </th>
                <th style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #dee2e6' }}>
                  90-100% Loss
                </th>
                <th style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #dee2e6' }}>
                  100%+ Loss
                </th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(transformResult.results).map(([scenario, data]) => {
                console.log(`Debug: Scenario ${scenario} data:`, data);
                console.log(`Debug: Scenario ${scenario} loss_distribution:`, data.loss_distribution);
                return (
                <tr key={scenario} style={{ borderBottom: '1px solid #dee2e6' }}>
                  <td style={{ 
                    padding: '12px', 
                    fontWeight: '600',
                    color: '#000000'
                  }}>
                    {getScenarioDisplayName(scenario)}
                  </td>
                  <td style={{ 
                    padding: '12px', 
                    textAlign: 'right',
                    fontFamily: 'monospace',
                    fontWeight: '600'
                  }}>
                    ${data.total_loan_amount.toLocaleString('en-US', { 
                      minimumFractionDigits: 0, 
                      maximumFractionDigits: 0 
                    })}
                  </td>
                  <td style={{ 
                    padding: '12px', 
                    textAlign: 'right',
                    fontFamily: 'monospace',
                    fontWeight: '600',
                    color: data.total_net_return >= 0 ? '#28a745' : '#dc3545'
                  }}>
                    ${data.total_net_return.toLocaleString('en-US', { 
                      minimumFractionDigits: 0, 
                      maximumFractionDigits: 0 
                    })}
                  </td>
                  <td style={{ 
                    padding: '12px', 
                    textAlign: 'right',
                    fontFamily: 'monospace',
                    fontWeight: '600',
                    color: data.positive_return_rate >= 50 ? '#28a745' : '#dc3545'
                  }}>
                    {data.positive_return_rate.toFixed(2)}%
                  </td>
                  <td style={{ 
                    padding: '12px', 
                    textAlign: 'right',
                    fontFamily: 'monospace',
                    fontWeight: '600',
                    color: data.irr_yearly >= 0 ? '#28a745' : '#dc3545'
                  }}>
                    {(data.irr_yearly * 100)?.toFixed(2) || 'N/A'}%
                  </td>
                  <td style={{ 
                    padding: '12px', 
                    textAlign: 'right',
                    fontFamily: 'monospace',
                    fontWeight: '600',
                    fontSize: '12px'
                  }}>
                    {(() => {
                      console.log('Debug: Loss distribution data for 0-10%:', data.loss_distribution?.['0-10%']);
                      return data.loss_distribution?.['0-10%']?.[1]?.toFixed(2) || '0.00';
                    })()}%
                  </td>
                  <td style={{ 
                    padding: '12px', 
                    textAlign: 'right',
                    fontFamily: 'monospace',
                    fontWeight: '600',
                    fontSize: '12px'
                  }}>
                    {data.loss_distribution?.['10-20%']?.[1]?.toFixed(2) || '0.00'}%
                  </td>
                  <td style={{ 
                    padding: '12px', 
                    textAlign: 'right',
                    fontFamily: 'monospace',
                    fontWeight: '600',
                    fontSize: '12px'
                  }}>
                    {data.loss_distribution?.['20-30%']?.[1]?.toFixed(2) || '0.00'}%
                  </td>
                  <td style={{ 
                    padding: '12px', 
                    textAlign: 'right',
                    fontFamily: 'monospace',
                    fontWeight: '600',
                    fontSize: '12px'
                  }}>
                    {data.loss_distribution?.['30-40%']?.[1]?.toFixed(2) || '0.00'}%
                  </td>
                  <td style={{ 
                    padding: '12px', 
                    textAlign: 'right',
                    fontFamily: 'monospace',
                    fontWeight: '600',
                    fontSize: '12px'
                  }}>
                    {data.loss_distribution?.['40-50%']?.[1]?.toFixed(2) || '0.00'}%
                  </td>
                  <td style={{ 
                    padding: '12px', 
                    textAlign: 'right',
                    fontFamily: 'monospace',
                    fontWeight: '600',
                    fontSize: '12px'
                  }}>
                    {data.loss_distribution?.['50-60%']?.[1]?.toFixed(2) || '0.00'}%
                  </td>
                  <td style={{ 
                    padding: '12px', 
                    textAlign: 'right',
                    fontFamily: 'monospace',
                    fontWeight: '600',
                    fontSize: '12px'
                  }}>
                    {data.loss_distribution?.['60-70%']?.[1]?.toFixed(2) || '0.00'}%
                  </td>
                  <td style={{ 
                    padding: '12px', 
                    textAlign: 'right',
                    fontFamily: 'monospace',
                    fontWeight: '600',
                    fontSize: '12px'
                  }}>
                    {data.loss_distribution?.['70-80%']?.[1]?.toFixed(2) || '0.00'}%
                  </td>
                  <td style={{ 
                    padding: '12px', 
                    textAlign: 'right',
                    fontFamily: 'monospace',
                    fontWeight: '600',
                    fontSize: '12px'
                  }}>
                    {data.loss_distribution?.['80-90%']?.[1]?.toFixed(2) || '0.00'}%
                  </td>
                  <td style={{ 
                    padding: '12px', 
                    textAlign: 'right',
                    fontFamily: 'monospace',
                    fontWeight: '600',
                    fontSize: '12px'
                  }}>
                    {data.loss_distribution?.['90-100%']?.[1]?.toFixed(2) || '0.00'}%
                  </td>
                  <td style={{ 
                    padding: '12px', 
                    textAlign: 'right',
                    fontFamily: 'monospace',
                    fontWeight: '600',
                    fontSize: '12px'
                  }}>
                    {data.loss_distribution?.['100%+']?.[1]?.toFixed(2) || '0.00'}%
                  </td>
                </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
} 