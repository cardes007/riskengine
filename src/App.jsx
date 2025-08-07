import React, { useState, useEffect, useMemo, useCallback } from 'react';
import PLForm from './components/PLForm';
import CohortForm from './components/CohortForm';
import BackendIntegration from './components/BackendIntegration';
import NDREvolutionChart from './components/NDREvolutionChart';
import IRRDisplay from './components/IRRDisplay';
import EBITDAMarginChart from './components/EBITDAMarginChart';
import NDRTable from './components/NDRTable';
import BackendDebug from './components/BackendDebug';
import './App.css';

const ALL_MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

function getDefaultSettings() {
  const now = new Date();
  let lastMonthIdx = now.getMonth() - 1;
  let year = now.getFullYear();
  if (lastMonthIdx < 0) {
    lastMonthIdx = 11;
    year--;
  }
  return {
    numMonths: 12,
    lastMonthIdx,
    year,
  };
}

function getAbbrevMonthLabel(monthIdx, year) {
  const month = ALL_MONTHS[monthIdx].slice(0, 3);
  const yr = String(year).slice(-2);
  return `${month} ${yr}`;
}

function getMonthLabels(numMonths, lastMonthIdx, year) {
  const months = [];
  let m = lastMonthIdx;
  let y = year;
  for (let i = 0; i < numMonths; i++) {
    months.unshift({
      label: `${ALL_MONTHS[m]} ${y}`,
      abbrev: getAbbrevMonthLabel(m, y),
      monthIdx: m,
      year: y,
    });
    m--;
    if (m < 0) {
      m = 11;
      y--;
    }
  }
  return months;
}

function App() {
  const [settings, setSettings] = useState(getDefaultSettings());
  const monthLabels = useMemo(() => getMonthLabels(settings.numMonths, settings.lastMonthIdx, settings.year), [settings.numMonths, settings.lastMonthIdx, settings.year]);
  const [showConclusions, setShowConclusions] = useState(false);
  const [ndrTable, setNdrTable] = useState(null);

  // Memoize data loading to prevent unnecessary re-renders
  const { plData, cohortData } = useMemo(() => {
    try {
      const plDataRaw = localStorage.getItem('plData');
      const cohortDataRaw = localStorage.getItem('cohortData');
      
      const plData = plDataRaw ? JSON.parse(plDataRaw) : [];
      const cohortData = cohortDataRaw ? JSON.parse(cohortDataRaw) : [];
      
      return { plData, cohortData };
    } catch (error) {
      console.error('Error loading data from localStorage:', error);
      return { plData: [], cohortData: [] };
    }
  }, []);

  // Auto-trigger analysis when data is available
  useEffect(() => {
    // Check if we have P&L data and cohort data
    if (plData && cohortData && Array.isArray(plData) && plData.length > 0 && 
        Array.isArray(cohortData) && cohortData.length > 0) {
      console.log('Auto-triggering analysis - data found in localStorage');
      setShowConclusions(true);
      setNdrTable(computeNDRTable());
    }
  }, [plData, cohortData]); // Run when data changes

  // Helper to compute NDR table from cohort data - memoized
  const computeNDRTable = useCallback(() => {
    if (!Array.isArray(cohortData) || cohortData.length === 0) return null;
    
    // Defensive: ensure each row has a revenue array
    return cohortData.map(row => {
      const base = Array.isArray(row.revenue) ? row.revenue : [];
      const denom = parseFloat(base[0]); // <-- use first column
      return {
        name: row.name,
        ndr: base.map((val, idx) => {
          const num = parseFloat(val);
          if (!isFinite(num) || !isFinite(denom) || denom === 0) return '';
          return Math.round(num / denom * 100) + '%';
        })
      };
    });
  }, [cohortData]);

  return (
    <div className="app-container">
      <h1>Risk Engine</h1>
      <div style={{ maxWidth: 900, margin: '0 auto' }}>
        <PLForm
          settings={settings}
          setSettings={setSettings}
          monthLabels={monthLabels}
        />
        <div style={{ marginTop: 40 }}>
          <CohortForm
            monthLabels={monthLabels}
          />
        </div>
        
        {/* Backend Debug Component - Remove this in production */}
        <BackendDebug />
        
        {/* Backend Integration Component */}
        <BackendIntegration 
          plData={plData}
          cohortData={cohortData}
        />
        
        {/* IRR Display Component */}
        <IRRDisplay />
        <div style={{ marginTop: 32, textAlign: 'center' }}>
          <button
            onClick={() => {
              setShowConclusions(true);
              setNdrTable(computeNDRTable());
            }}
            style={{ fontSize: 18, padding: '10px 32px', margin: '24px 0' }}
          >
            Analyze Data
          </button>
        </div>
        {showConclusions && (
          <div style={{ marginTop: 32 }}>
            <h2>Net Dollar Retention (NDR) Analysis</h2>
            {/* 1. NDR Table */}
            {ndrTable && ndrTable.length > 0 && (
              <NDRTable 
                ndrTable={ndrTable}
                monthLabels={monthLabels}
                cohortData={cohortData}
              />
            )}
            
            {/* NDR Evolution Chart */}
            <NDREvolutionChart />
          </div>
        )}
      </div>
      
      {/* Simplified tables - only render if data exists */}
      {cohortData && cohortData.length > 0 && (
        <>
          {/* 3. Gross Profit Cohorts Table */}
          <h2 style={{ marginBottom: 18, marginTop: 48 }}>Gross Profit Cohorts</h2>
          <table className="pl-table">
            <thead>
              <tr>
                <th>Cohort</th>
                {monthLabels.map((_, idx) => <th key={idx}>{idx + 1}</th>)}
              </tr>
            </thead>
            <tbody>
              {cohortData.slice(1).map((cohort, cohortIdx) => (
                <tr key={cohort.name}>
                  <td style={{ fontWeight: 600 }}>{cohort.name}</td>
                  {monthLabels.map((_, monthIdx) => {
                    const numCols = monthLabels.length;
                    const trueCohortIdx = cohortIdx + 1;
                    const allowInput = monthIdx <= numCols - trueCohortIdx - 1 || trueCohortIdx + monthIdx === numCols - 1 || trueCohortIdx + monthIdx === numCols;
                    
                    // Simplified gross margin calculation
                    const grossMargins = plData.map(row => {
                      const revenue = parseFloat(row && row.revenue);
                      const grossProfit = parseFloat(row && row.grossProfit);
                      return (isFinite(revenue) && revenue !== 0 && isFinite(grossProfit)) ? (grossProfit / revenue) : null;
                    });
                    
                    const enabledIndices = [];
                    for (let i = 0; i < numCols; i++) {
                      const enabled = i <= numCols - trueCohortIdx - 1 || trueCohortIdx + i === numCols - 1 || trueCohortIdx + i === numCols;
                      if (enabled) enabledIndices.push(i);
                    }
                    
                    let grossMargin = null;
                    if (allowInput) {
                      const idxInEnabled = enabledIndices.indexOf(monthIdx);
                      if (idxInEnabled !== -1) {
                        const grossMarginIdx = grossMargins.length - enabledIndices.length + idxInEnabled;
                        grossMargin = grossMargins[grossMarginIdx];
                      }
                    }
                    
                    const cohortRev = Array.isArray(cohort.revenue) && cohort.revenue[monthIdx] !== undefined ? parseFloat(cohort.revenue[monthIdx]) : NaN;
                    let val = '';
                    if (grossMargin !== null && isFinite(cohortRev)) {
                      val = Math.round(grossMargin * cohortRev);
                    }
                    
                    return (
                      <td key={monthIdx} style={!allowInput ? { background: '#f3f3f3' } : {}}>
                        {allowInput && val !== '' && isFinite(Number(val)) ? val : ''}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
      
      {/* EBITDA Margin Chart */}
      <h2 style={{ marginBottom: '18px', marginTop: '48px' }}>EBITCAC Evolution</h2>
      <EBITDAMarginChart />

      {/* After the NDR table rendering, add the following explanatory note: */}
      <div style={{ maxWidth: 900, margin: '24px auto 0 auto', fontSize: 15, color: '#444', background: '#f7f7fa', borderRadius: 8, padding: '16px 24px', border: '1px solid #e0e0e0', textAlign: 'left' }}>
        <strong>Notes:</strong>
        <ul style={{ margin: 0, paddingLeft: 24 }}>
          <li>The <strong>Forecast Curve</strong> is calculated using the weighted average retention of the last 12 months of available data in every column.</li>
          <li>The <strong>Conservative Forecast</strong> is calculated as the minimum of the median, simple avg, weighted avg, yearly weighted avgs, and forecast curve for every column, and only computes if at least 4 of the above are available.</li>
          <li>The S&M / New Rev statistics calculations exclude months in which there is no acquisition.</li>
        </ul>
      </div>
    </div>
  );
}

export default App;
