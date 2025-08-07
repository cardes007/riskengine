import React, { useState, useEffect } from 'react';
import PLForm from './components/PLForm';
import CohortForm from './components/CohortForm';
import BackendIntegration from './components/BackendIntegration';
import NDREvolutionChart from './components/NDREvolutionChart';
import IRRDisplay from './components/IRRDisplay';
import EBITDAMarginChart from './components/EBITDAMarginChart';
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
  const monthLabels = getMonthLabels(settings.numMonths, settings.lastMonthIdx, settings.year);
  const [showConclusions, setShowConclusions] = useState(false);
  const [ndrTable, setNdrTable] = useState(null);
  const [rollingAvgVals, setRollingAvgVals] = useState([]);

  useEffect(() => {
    if (rollingAvgVals.length > 0) {
      fetchFitDistribution(rollingAvgVals)
        .then(setFitResult)
        .catch(err => setFitError(err.message));
    }
  }, [rollingAvgVals]);

  // Auto-trigger analysis when data is available
  useEffect(() => {
    // Check if we have P&L data and cohort data
    const plData = localStorage.getItem('plData');
    const cohortData = localStorage.getItem('cohortData');
    
    if (plData && cohortData) {
      try {
        const parsedPLData = JSON.parse(plData);
        const parsedCohortData = JSON.parse(cohortData);
        
        // If we have valid data, automatically trigger analysis
        if (Array.isArray(parsedPLData) && parsedPLData.length > 0 && 
            Array.isArray(parsedCohortData) && parsedCohortData.length > 0) {
          console.log('Auto-triggering analysis - data found in localStorage');
          setShowConclusions(true);
          setNdrTable(computeNDRTable());
        }
      } catch (error) {
        console.error('Error auto-triggering analysis:', error);
      }
    }
  }, []); // Run once on mount

  // Helper to compute NDR table from cohort data
  function computeNDRTable() {
    const cohortDataRaw = localStorage.getItem('cohortData');
    let cohortData = [];
    try {
      cohortData = JSON.parse(cohortDataRaw) || [];
    } catch {
      cohortData = [];
    }
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
  }

  // Helper to get background color for NDR cell
  function getNDRColor(val) {
    if (!val || typeof val !== 'string' || !val.endsWith('%')) return '#f3f3f3';
    const pct = parseFloat(val);
    if (!isFinite(pct)) return '#f3f3f3';
    if (pct >= 100) return '#eaf3ea'; // green
    if (pct >= 80) return '#fffbe6'; // yellow
    if (pct >= 0) return '#fdeaea'; // red
    return '#f3f3f3';
  }

  // Helper to compute simple and weighted averages for each NDR column
  function getNDRSummaryRows(ndrTable, cohortData, monthLabels) {
    if (!ndrTable || ndrTable.length === 0) return { simple: [], weighted: [], median: [] };
    const numCols = monthLabels.length;
    // Simple average: mean of all numeric NDR values in each column (excluding blanks)
    const simple = [];
    for (let col = 0; col < numCols; col++) {
      let sum = 0, count = 0;
      for (let row = 1; row < ndrTable.length; row++) { // skip first row (Older Cohorts)
        const val = ndrTable[row].ndr[col];
        const pct = parseFloat(val);
        if (isFinite(pct)) {
          sum += pct;
          count++;
        }
      }
      simple.push(count >= 6 ? Math.round(sum / count) + '%' : '');
    }
    // Median: median of all numeric NDR values in each column (excluding blanks)
    function median(values) {
      if (!values.length) return '';
      const sorted = [...values].sort((a, b) => a - b);
      const mid = Math.floor(sorted.length / 2);
      if (sorted.length % 2 !== 0) {
        return Math.round(sorted[mid]) + '%';
      } else {
        return Math.round((sorted[mid - 1] + sorted[mid]) / 2) + '%';
      }
    }
    const medianArr = [];
    for (let col = 0; col < numCols; col++) {
      const colVals = [];
      for (let row = 1; row < ndrTable.length; row++) { // skip first row (Older Cohorts)
        const val = ndrTable[row].ndr[col];
        const pct = parseFloat(val);
        if (isFinite(pct)) {
          colVals.push(pct);
        }
      }
      medianArr.push(colVals.length >= 6 ? median(colVals) : '');
    }
    // Weighted average: sum of all cohort revenues for that month / sum of all cohort revenues for first month
    const weighted = [];
    if (Array.isArray(cohortData) && cohortData.length > 1) {
      for (let col = 0; col < numCols; col++) {
        let numer = 0, denom = 0, count = 0;
        for (let row = 1; row < cohortData.length; row++) { // skip first row (Older Cohorts)
          const base = Array.isArray(cohortData[row].revenue) ? cohortData[row].revenue : [];
          const v = parseFloat(base[col]);
          const v0 = parseFloat(base[0]);
          if (isFinite(v) && isFinite(v0) && v0 !== 0) {
            numer += v;
            denom += v0;
            count++;
          }
        }
        weighted.push((denom > 0 && count >= 6) ? Math.round(numer / denom * 100) + '%' : '');
      }
    } else {
      for (let col = 0; col < numCols; col++) weighted.push('');
    }
    return { simple, weighted, median: medianArr };
  }

  // Helper to compute yearly weighted average NDR rows (apples-to-apples logic)
  function getYearlyWeightedRows(cohortData, monthLabels) {
    if (!Array.isArray(cohortData) || cohortData.length <= 1) return [];
    // Map: year -> array of cohort indices (skip Older Cohorts)
    const yearToCohorts = {};
    for (let row = 1; row < cohortData.length; row++) {
      const cohortName = cohortData[row].name;
      const cohortStartIdx = monthLabels.findIndex(m => m.abbrev === cohortName);
      const cohortStartYear = cohortStartIdx !== -1 ? monthLabels[cohortStartIdx].year : null;
      if (cohortStartYear !== null) {
        if (!yearToCohorts[cohortStartYear]) yearToCohorts[cohortStartYear] = [];
        yearToCohorts[cohortStartYear].push({ row, cohortStartIdx });
      }
    }
    const years = Object.keys(yearToCohorts).sort();
    const numCols = monthLabels.length;
    const rows = [];
    for (const year of years) {
      const cohortInfos = yearToCohorts[year];
      const vals = Array(numCols).fill('');
      for (let col = 0; col < numCols; col++) {
        let numer = 0, denom = 0, count = 0;
        for (const info of cohortInfos) {
          const base = Array.isArray(cohortData[info.row].revenue) ? cohortData[info.row].revenue : [];
          const v = parseFloat(base[col]);
          const v0 = parseFloat(base[0]);
          if (isFinite(v) && isFinite(v0) && v0 !== 0) {
            numer += v;
            denom += v0;
            count++;
          }
        }
        vals[col] = (denom > 0 && count >= 3) ? Math.round(numer / denom * 100) + '%' : '';
      }
      // Format label as W.Avg 'YY
      const yearStr = String(year);
      const shortYear = yearStr.length > 2 ? yearStr.slice(-2) : yearStr;
      rows.push({ year, vals, label: `W.Avg '${shortYear}` });
    }
    return rows;
  }

  // Helper to render a simple SVG line chart for the average rows
  function NDRLineChart({ monthLabels, summary, yearlyRows, forecastCurve, conservativeCurve }) {
    const parseRow = arr => arr.map(v => {
      const n = parseFloat(v);
      return isFinite(n) ? n : null;
    });
    // Add Median NDR to the series
    const baseSeries = [
      { label: 'Simple Avg', color: '#1976d2', data: parseRow(summary.simple) },
      { label: 'Weighted Avg', color: '#43a047', data: parseRow(summary.weighted) },
      { label: 'Median NDR', color: '#ff9800', data: parseRow(summary.median) },
      ...yearlyRows.map((row, i) => ({
        label: row.label || `W.Avg '${String(row.year).slice(-2)}`,
        color: ['#e53935', '#fbc02d', '#8e24aa', '#00897b', '#6d4c41'][i % 5],
        data: parseRow(row.vals)
      })),
      { label: 'Forecast Curve', color: '#0080ff', data: parseRow(forecastCurve) },
      { label: 'Conservative Forecast', color: '#444', data: parseRow(conservativeCurve) }
    ];
    // State for toggling series
    const [enabled, setEnabled] = React.useState(() => baseSeries.map(() => true));
    React.useEffect(() => {
      setEnabled(baseSeries.map(() => true)); // reset toggles if series count changes
    }, [monthLabels.length, yearlyRows.length]);
    const width = Math.max(60 * monthLabels.length, 900);
    const height = 600; // Increased height for better visibility
    const shownSeries = baseSeries.filter((_, i) => enabled[i]);
    const allVals = shownSeries.flatMap(s => s.data).filter(v => v !== null);
    const maxY = allVals.length > 0 ? Math.max(...allVals) : 1;
    const minY = allVals.length > 0 ? Math.min(...allVals) : 0;
    const x = idx => 40 + idx * (width - 60) / (monthLabels.length - 1);
    const y = v => height - 30 - ((v - minY) / (maxY - minY || 1)) * (height - 60);
    function smoothLinePath(data) {
      let d = '';
      let last = null;
      for (let i = 0; i < data.length; i++) {
        const v = data[i];
        if (v === null) continue;
        const cx = x(i), cy = y(v);
        if (last === null) {
          d += `M ${cx} ${cy}`;
        } else {
          const prevX = x(last.i), prevY = y(last.v);
          const c1x = prevX + (cx - prevX) / 2;
          const c1y = prevY;
          const c2x = prevX + (cx - prevX) / 2;
          const c2y = cy;
          d += ` C ${c1x} ${c1y}, ${c2x} ${c2y}, ${cx} ${cy}`;
        }
        last = { i, v };
      }
      return d;
    }
    return (
      <div style={{ margin: '32px 0 0 0', width: '100%' }}>
        <div style={{ background: '#fff', border: '1px solid #eee', borderRadius: 12, boxShadow: '0 2px 12px #0001', padding: 16, position: 'relative', width: width }}>
          {/* Radio buttons for toggling curves */}
          <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap', marginBottom: 12, fontSize: 15, alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ fontWeight: 600, color: '#444', marginRight: 8 }}>Show curves:</span>
            {baseSeries.map((s, i) => (
              <label key={s.label} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={enabled[i]}
                  onChange={() => setEnabled(en => en.map((v, idx) => idx === i ? !v : v))}
                  style={{ accentColor: s.color, width: 16, height: 16 }}
                />
                <span style={{ width: 18, height: 3, background: s.color, display: 'inline-block', borderRadius: 2 }} />
                {s.label}
              </label>
            ))}
          </div>
          <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} style={{ display: 'block' }}>
            {/* Y axis grid and ticks */}
            {[minY, (minY+maxY)/2, maxY].map((tick, i) => (
              <g key={i}>
                <line x1={35} x2={width-15} y1={y(tick)} y2={y(tick)} stroke="#eee" />
                <text x={10} y={y(tick)+4} fontSize={12} fill="#888">{Math.round(tick)}%</text>
              </g>
            ))}
            {/* X axis labels */}
            {monthLabels.map((m, i) => (
              <text key={i} x={x(i)} y={height-10} fontSize={12} fill="#888" textAnchor="middle">{i+1}</text>
            ))}
            {/* Y axis label */}
            <text x={-height/2} y={16} fontSize={13} fill="#888" textAnchor="middle" transform={`rotate(-90 16,${height/2})`}>NDR %</text>
            {/* X axis label */}
            <text x={width/2} y={height-2} fontSize={13} fill="#888" textAnchor="middle">Month</text>
            {/* Lines (smooth) */}
            {shownSeries.map((s, i) => (
              <path key={s.label} d={smoothLinePath(s.data)} fill="none" stroke={s.color} strokeWidth={2.5} />
            ))}
            {/* Dots with white border */}
            {shownSeries.map((s, i) => s.data.map((v, j) => v === null ? null : (
              <circle key={i+'-'+j} cx={x(j)} cy={y(v)} r={5} fill="#fff" stroke={s.color} strokeWidth={2.5} />
            )))}
          </svg>
          <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap', marginTop: 8, fontSize: 14, justifyContent: 'center' }}>
            <span style={{ fontWeight: 600, color: '#444', marginRight: 8 }}>Legend:</span>
            {shownSeries.map(s => (
              <span key={s.label} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <span style={{ width: 18, height: 3, background: s.color, display: 'inline-block', borderRadius: 2 }} />
                {s.label}
              </span>
            ))}
          </div>
        </div>
      </div>
    );
  }

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
        
        {/* Backend Integration Component */}
        <BackendIntegration 
          plData={(() => {
            try {
              const data = JSON.parse(localStorage.getItem('plData')) || [];
              console.log('P&L Data loaded from localStorage:', data);
              console.log('P&L Data length in App:', data?.length);
              console.log('P&L Data sample:', data?.slice(0, 2));
              return data;
            } catch (error) {
              console.error('Error loading P&L data from localStorage:', error);
              return [];
            }
          })()}
          cohortData={(() => {
            try {
              const data = JSON.parse(localStorage.getItem('cohortData')) || [];
              console.log('Cohort Data loaded from localStorage:', data);
              console.log('Cohort Data length in App:', data?.length);
              return data;
            } catch (error) {
              console.error('Error loading cohort data from localStorage:', error);
              return [];
            }
          })()}
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
            {ndrTable && ndrTable.length > 0 && (() => {
              // Get cohortData for weighted average
              let cohortData = [];
              try {
                cohortData = JSON.parse(localStorage.getItem('cohortData')) || [];
              } catch { cohortData = []; }
              const summary = getNDRSummaryRows(ndrTable, cohortData, monthLabels);
              const yearlyRows = getYearlyWeightedRows(cohortData, monthLabels);
              // Forecast Curve calculation (same as in table row)
              const cohortRows = cohortData.slice(1);
              const numCols = monthLabels.length;
              const forecastCurve = [];
              forecastCurve.push('100%');
              for (let col = 1; col < numCols; col++) {
                // For the 11 rightmost columns, always show blank
                if (col > numCols - 12) {
                  forecastCurve.push('');
                  continue;
                }
                const enabledRows = cohortRows
                  .map((row, cohortIdx) => {
                    const allowInput = col <= numCols - (cohortIdx + 1) - 1 || (cohortIdx + 1) + col === numCols - 1 || (cohortIdx + 1) + col === numCols;
                    return allowInput ? { row, cohortIdx } : null;
                  })
                  .filter(x => x !== null);
                const last12 = enabledRows.slice(-12);
                const numerArr = last12.map(({ row }) => parseFloat(row.revenue[col])).filter(v => isFinite(v));
                const denomArr = last12.map(({ row }) => parseFloat(row.revenue[0])).filter(v => isFinite(v));
                const numer = numerArr.reduce((a, b) => a + b, 0);
                const denom = denomArr.reduce((a, b) => a + b, 0);
                let val = '';
                if (denom > 0 && numerArr.length === 12 && denomArr.length === 12) {
                  val = Math.round(numer / denom * 100) + '%';
                }
                forecastCurve.push(val);
              }
              // Conservative Forecast Curve: min of Median NDR, all yearly weighted avg rows, and Forecast Curve
              const minCurve = [];
              minCurve.push('100%');
              for (let col = 1; col < numCols; col++) {
                const vals = [];
                // Median NDR
                const medianVal = parseFloat(summary.median[col]);
                if (isFinite(medianVal)) vals.push(medianVal);
                // Simple Avg
                const simpleVal = parseFloat(summary.simple[col]);
                if (isFinite(simpleVal)) vals.push(simpleVal);
                // Weighted Avg
                const weightedVal = parseFloat(summary.weighted[col]);
                if (isFinite(weightedVal)) vals.push(weightedVal);
                // Forecast Curve
                const forecastVal = parseFloat(forecastCurve[col]);
                if (isFinite(forecastVal)) vals.push(forecastVal);
                // All yearly weighted avg rows
                for (const row of yearlyRows) {
                  const v = parseFloat(row.vals[col]);
                  if (isFinite(v)) vals.push(v);
                }
                let minVal = '';
                if (vals.length >= 4) {
                  minVal = Math.round(Math.min(...vals)) + '%';
                }
                minCurve.push(minVal);
              }
              return (
                <>
                  <table className="pl-table" style={{ marginBottom: 0 }}>
                    <thead>
                      <tr>
                        <th>Cohort</th>
                        {monthLabels.map((_, idx) => <th key={idx}>{idx + 1}</th>)}
                      </tr>
                    </thead>
                    <tbody>
                      {ndrTable.map((row, cohortIdx) => (
                        <tr key={row.name}>
                          <td style={{ fontWeight: cohortIdx === 0 ? 700 : 600 }}>{row.name}</td>
                          {monthLabels.map((_, monthIdx) => (
                            <td key={monthIdx} style={{ background: getNDRColor(row.ndr[monthIdx]) }}>
                              {row.ndr[monthIdx]}
                            </td>
                          ))}
                        </tr>
                      ))}
                      <tr>
                        <td style={{ fontWeight: 700, background: '#f7f7fa' }}>Median NDR</td>
                        {summary.median.map((val, idx) => (
                          <td key={idx} style={{ background: getNDRColor(val), fontWeight: 700 }}>{val}</td>
                        ))}
                      </tr>
                      <tr>
                        <td style={{ fontWeight: 700, background: '#f7f7fa' }}>Simple Avg</td>
                        {summary.simple.map((val, idx) => (
                          <td key={idx} style={{ background: getNDRColor(val), fontWeight: 700 }}>{val}</td>
                        ))}
                      </tr>
                      <tr>
                        <td style={{ fontWeight: 700, background: '#f7f7fa' }}>Weighted Avg</td>
                        {summary.weighted.map((val, idx) => (
                          <td key={idx} style={{ background: getNDRColor(val), fontWeight: 700 }}>{val}</td>
                        ))}
                      </tr>
                      {yearlyRows.map(row => (
                        <tr key={row.year}>
                          <td style={{ fontWeight: 700, background: '#f7f7fa' }}>{row.label || `W.Avg '${String(row.year).slice(-2)}`}</td>
                          {row.vals.map((val, idx) => (
                            <td key={idx} style={{ background: getNDRColor(val), fontWeight: 700 }}>{val}</td>
                          ))}
                        </tr>
                      ))}
                      {/* Forecast Curve Row */}
                      <tr>
                        <td style={{ fontWeight: 700, background: '#f7f7fa' }}>Forecast Curve</td>
                        {forecastCurve.map((val, idx) => (
                          <td key={idx} style={{ background: getNDRColor(val), fontWeight: 700 }}>{val}</td>
                        ))}
                      </tr>
                      <tr>
                        <td style={{ fontWeight: 700, background: '#f7f7fa' }}>Conservative Forecast</td>
                        {minCurve.map((val, idx) => (
                          <td key={idx} style={{ background: getNDRColor(val), fontWeight: 700 }}>{val}</td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                  <NDRLineChart monthLabels={monthLabels} summary={summary} yearlyRows={yearlyRows} 
                    forecastCurve={forecastCurve} conservativeCurve={minCurve}
                  />
                  
                  {/* NDR Evolution Chart */}
                  <NDREvolutionChart />
                </>
              );
            })()}
          </div>
        )}
      </div>
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
          {(() => {
            // Build cohort rows: first is 'Older Cohorts', then each cohort by month
            let cohortData = [];
            let plData = [];
            try {
              cohortData = JSON.parse(localStorage.getItem('cohortData')) || [];
            } catch { cohortData = []; }
            try {
              plData = JSON.parse(localStorage.getItem('plData')) || [];
            } catch { plData = []; }
            // Defensive: ensure structure
            if (!Array.isArray(cohortData) || cohortData.length === 0) return null;
            return cohortData.slice(1).map((cohort, cohortIdx) => (
              <tr key={cohort.name}>
                <td style={{ fontWeight: 600 }}>{cohort.name}</td>
                {monthLabels.map((_, monthIdx) => {
                  const numCols = monthLabels.length;
                  // Diagonal/greyed-out logic (offset cohortIdx by 1 to match revenue cohorts)
                  const trueCohortIdx = cohortIdx + 1;
                  const allowInput = monthIdx <= numCols - trueCohortIdx - 1 || trueCohortIdx + monthIdx === numCols - 1 || trueCohortIdx + monthIdx === numCols;
                  // Precompute gross margins for all months
                  const grossMargins = plData.map(row => {
                    const revenue = parseFloat(row && row.revenue);
                    const grossProfit = parseFloat(row && row.grossProfit);
                    return (isFinite(revenue) && revenue !== 0 && isFinite(grossProfit)) ? (grossProfit / revenue) : null;
                  });
                  // Find all enabled cell indices for this row
                  const enabledIndices = [];
                  for (let i = 0; i < numCols; i++) {
                    const enabled = i <= numCols - trueCohortIdx - 1 || trueCohortIdx + i === numCols - 1 || trueCohortIdx + i === numCols;
                    if (enabled) enabledIndices.push(i);
                  }
                  // For enabled cells, assign gross margin from the last N months, rightmost gets most recent
                  let grossMargin = null;
                  if (allowInput) {
                    const idxInEnabled = enabledIndices.indexOf(monthIdx);
                    if (idxInEnabled !== -1) {
                      const grossMarginIdx = grossMargins.length - enabledIndices.length + idxInEnabled;
                      grossMargin = grossMargins[grossMarginIdx];
                    }
                  }
                  // Get cohort revenue for this cell
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
            ));
          })()}
        </tbody>
      </table>
      {/* 4. Cohort Payback Table */}
      <h2 style={{ marginBottom: 18, marginTop: 48 }}>Cohort Payback Table</h2>
      <table className="pl-table">
        <thead>
          <tr>
            <th>Cohort</th>
            <th>S&M</th>
            {monthLabels.map((_, idx) => <th key={idx}>{idx + 1}</th>)}
          </tr>
        </thead>
        <tbody>
          {(() => {
            let cohortData = [];
            let plData = [];
            try {
              cohortData = JSON.parse(localStorage.getItem('cohortData')) || [];
            } catch { cohortData = []; }
            try {
              plData = JSON.parse(localStorage.getItem('plData')) || [];
            } catch { plData = []; }
            if (!Array.isArray(cohortData) || cohortData.length === 0) return null;
            return cohortData.slice(1).map((cohort, cohortIdx) => {
              const numCols = monthLabels.length;
              const trueCohortIdx = cohortIdx + 1;
              // Precompute gross margins for all months (same as gross profit cohort table)
              const grossMargins = plData.map(row => {
                const revenue = parseFloat(row && row.revenue);
                const grossProfit = parseFloat(row && row.grossProfit);
                return (isFinite(revenue) && revenue !== 0 && isFinite(grossProfit)) ? (grossProfit / revenue) : null;
              });
              // Find all enabled cell indices for this row
              const enabledIndices = [];
              for (let i = 0; i < numCols; i++) {
                const enabled = i <= numCols - trueCohortIdx - 1 || trueCohortIdx + i === numCols - 1 || trueCohortIdx + i === numCols;
                if (enabled) enabledIndices.push(i);
              }
              // Precompute gross profit values for this row (identical to gross profit cohort table)
              const grossProfits = enabledIndices.map((monthIdx, idxInEnabled) => {
                const grossMarginIdx = grossMargins.length - enabledIndices.length + idxInEnabled;
                const grossMargin = grossMargins[grossMarginIdx];
                const cohortRev = Array.isArray(cohort.revenue) && cohort.revenue[monthIdx] !== undefined ? parseFloat(cohort.revenue[monthIdx]) : NaN;
                if (grossMargin !== null && isFinite(cohortRev)) {
                  return grossMargin * cohortRev;
                }
                return null;
              });
              // S&M spend for this cohort's start month
              const sm = plData[cohortIdx] && plData[cohortIdx].sm !== undefined ? parseFloat(plData[cohortIdx].sm) : '';
              // Now render the row
              return (
                <tr key={cohort.name}>
                  <td style={{ fontWeight: 600 }}>{cohort.name}</td>
                  <td style={{ fontWeight: 600 }}>
                    {sm !== '' && isFinite(sm)
                      ? `$${Math.round(sm).toLocaleString()}`
                      : ''}
                  </td>
                  {monthLabels.map((_, monthIdx) => {
                    // Diagonal/greyed-out logic
                    const allowInput = monthIdx <= numCols - trueCohortIdx - 1 || trueCohortIdx + monthIdx === numCols - 1 || trueCohortIdx + monthIdx === numCols;
                    let val = '';
                    if (allowInput) {
                      const idxInEnabled = enabledIndices.indexOf(monthIdx);
                      if (idxInEnabled !== -1) {
                        // Cumulative gross profit up to this cell (sum of grossProfits up to idxInEnabled)
                        const cumulativeGrossProfit = grossProfits.slice(0, idxInEnabled + 1).reduce((a, b) => a + (isFinite(b) ? b : 0), 0);
                        // S&M spend for this cohort's start month
                        const sm = plData[cohortIdx] && plData[cohortIdx].sm !== undefined ? parseFloat(plData[cohortIdx].sm) : NaN;
                        if (isFinite(sm) && sm !== 0) {
                          val = (cumulativeGrossProfit / sm).toFixed(2);
                        }
                      }
                    }
                    // Highlight the leftmost value > 1 in the row
                    let highlight = false;
                    if (allowInput && val !== '' && isFinite(Number(val)) && Number(val) > 1) {
                      // Check if this is the first value > 1 in this row
                      const isFirst = monthLabels.findIndex((_, idx) => {
                        if (!(idx in enabledIndices)) return false;
                        const idxInEnabled = enabledIndices.indexOf(idx);
                        if (idxInEnabled === -1) return false;
                        let v = '';
                        if (allowInput) {
                          const grossMarginIdx = grossMargins.length - enabledIndices.length + idxInEnabled;
                          const grossMargin = grossMargins[grossMarginIdx];
                          const cohortRev = Array.isArray(cohort.revenue) && cohort.revenue[idx] !== undefined ? parseFloat(cohort.revenue[idx]) : NaN;
                          if (grossMargin !== null && isFinite(cohortRev)) {
                            const grossProfitsUpTo = grossProfits.slice(0, idxInEnabled + 1).reduce((a, b) => a + (isFinite(b) ? b : 0), 0);
                            const sm = plData[cohortIdx] && plData[cohortIdx].sm !== undefined ? parseFloat(plData[cohortIdx].sm) : NaN;
                            if (isFinite(sm) && sm !== 0) {
                              v = (grossProfitsUpTo / sm).toFixed(2);
                            }
                          }
                        }
                        return v !== '' && isFinite(Number(v)) && Number(v) > 1;
                      });
                      if (isFirst === monthIdx) highlight = true;
                    }
                    return (
                      <td key={monthIdx} style={!allowInput ? { background: '#f3f3f3' } : highlight ? { background: '#ffe082' } : {}}>
                        {allowInput && val !== '' && isFinite(Number(val)) ? val : ''}
                      </td>
                    );
                  })}
                </tr>
              );
            });
          })()}
        </tbody>
      </table>
      {/* 5. Cohort Payback Chart */}
      {(() => {
        let cohortData = [];
        let plData = [];
        try {
          cohortData = JSON.parse(localStorage.getItem('cohortData')) || [];
        } catch { cohortData = []; }
        try {
          plData = JSON.parse(localStorage.getItem('plData')) || [];
        } catch { plData = []; }
        if (!Array.isArray(cohortData) || cohortData.length === 0) return null;
        // Prepare payback data for each cohort (excluding S&M column)
        const numCols = monthLabels.length;
        const paybackSeries = cohortData.slice(1).map((cohort, cohortIdx) => {
          const trueCohortIdx = cohortIdx + 1;
          // Diagonal/greyed-out logic
          const enabledIndices = [];
          for (let i = 0; i < numCols; i++) {
            const enabled = i <= numCols - trueCohortIdx - 1 || trueCohortIdx + i === numCols - 1 || trueCohortIdx + i === numCols;
            if (enabled) enabledIndices.push(i);
          }
          // Precompute gross profit values for this row (identical to gross profit cohort table)
          const grossMargins = plData.map(row => {
            const revenue = parseFloat(row && row.revenue);
            const grossProfit = parseFloat(row && row.grossProfit);
            return (isFinite(revenue) && revenue !== 0 && isFinite(grossProfit)) ? (grossProfit / revenue) : null;
          });
          const grossProfits = enabledIndices.map((monthIdx, idxInEnabled) => {
            const grossMarginIdx = grossMargins.length - enabledIndices.length + idxInEnabled;
            const grossMargin = grossMargins[grossMarginIdx];
            const cohortRev = Array.isArray(cohort.revenue) && cohort.revenue[monthIdx] !== undefined ? parseFloat(cohort.revenue[monthIdx]) : NaN;
            if (grossMargin !== null && isFinite(cohortRev)) {
              return grossMargin * cohortRev;
            }
            return null;
          });
          // S&M spend for this cohort's start month
          const sm = plData[cohortIdx] && plData[cohortIdx].sm !== undefined ? parseFloat(plData[cohortIdx].sm) : NaN;
          // Build payback values for each month (same as table)
          const paybackVals = monthLabels.map((_, monthIdx) => {
            const allowInput = monthIdx <= numCols - trueCohortIdx - 1 || trueCohortIdx + monthIdx === numCols - 1 || trueCohortIdx + monthIdx === numCols;
            if (!allowInput) return null;
            const idxInEnabled = enabledIndices.indexOf(monthIdx);
            if (idxInEnabled === -1) return null;
            if (!isFinite(sm) || sm === 0) return null;
            const cumulativeGrossProfit = grossProfits.slice(0, idxInEnabled + 1).reduce((a, b) => a + (isFinite(b) ? b : 0), 0);
            return parseFloat((cumulativeGrossProfit / sm).toFixed(1));
          });
          return {
            label: cohort.name,
            color: [
              '#1976d2', '#43a047', '#ff9800', '#e53935', '#8e24aa', '#00897b', '#6d4c41', '#fbc02d', '#0080ff', '#444'
            ][cohortIdx % 10],
            data: paybackVals
          };
        });
        // State for toggling series
        const [enabled, setEnabled] = React.useState(() => paybackSeries.map(() => true));
        React.useEffect(() => {
          setEnabled(paybackSeries.map(() => true));
        }, [monthLabels.length, cohortData.length]);
        const width = Math.max(60 * monthLabels.length, 900);
        const height = 600;
        const shownSeries = paybackSeries.filter((_, i) => enabled[i]);
        const allVals = shownSeries.flatMap(s => s.data).filter(v => v !== null);
        const maxY = allVals.length > 0 ? Math.max(...allVals) : 1;
        const minY = allVals.length > 0 ? Math.min(...allVals) : 0;
        const x = idx => 40 + idx * (width - 60) / (monthLabels.length - 1);
        const y = v => height - 30 - ((v - minY) / (maxY - minY || 1)) * (height - 60);
        function smoothLinePath(data) {
          let d = '';
          let last = null;
          for (let i = 0; i < data.length; i++) {
            const v = data[i];
            if (v === null) continue;
            const cx = x(i), cy = y(v);
            if (last === null) {
              d += `M ${cx} ${cy}`;
            } else {
              const prevX = x(last.i), prevY = y(last.v);
              const c1x = prevX + (cx - prevX) / 2;
              const c1y = prevY;
              const c2x = prevX + (cx - prevX) / 2;
              const c2y = cy;
              d += ` C ${c1x} ${c1y}, ${c2x} ${c2y}, ${cx} ${cy}`;
            }
            last = { i, v };
          }
          return d;
        }
        return (
          <div style={{ margin: '32px 0 0 0', width: '100%' }}>
            <div style={{ background: '#fff', border: '1px solid #eee', borderRadius: 12, boxShadow: '0 2px 12px #0001', padding: 16, position: 'relative', width: width }}>
              {/* Radio buttons for toggling curves */}
              <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap', marginBottom: 12, fontSize: 15, alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ fontWeight: 600, color: '#444', marginRight: 8 }}>Show cohorts:</span>
                {paybackSeries.map((s, i) => (
                  <label key={s.label} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={enabled[i]}
                      onChange={() => setEnabled(en => en.map((v, idx) => idx === i ? !v : v))}
                      style={{ accentColor: s.color, width: 16, height: 16 }}
                    />
                    <span style={{ width: 18, height: 3, background: s.color, display: 'inline-block', borderRadius: 2 }} />
                    {s.label}
                  </label>
                ))}
              </div>
              <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} style={{ display: 'block' }}>
                {/* Y axis grid and ticks */}
                {[minY, (minY+maxY)/2, maxY].map((tick, i) => (
                  <g key={i}>
                    <line x1={35} x2={width-15} y1={y(tick)} y2={y(tick)} stroke="#eee" />
                    <text x={10} y={y(tick)+4} fontSize={12} fill="#888">{tick.toFixed(1)}</text>
                  </g>
                ))}
                {/* X axis labels */}
                {monthLabels.map((m, i) => (
                  <text key={i} x={x(i)} y={height-10} fontSize={12} fill="#888" textAnchor="middle">{i+1}</text>
                ))}
                {/* Y axis label */}
                <text x={-height/2} y={16} fontSize={13} fill="#888" textAnchor="middle" transform={`rotate(-90 16,${height/2})`}>Payback</text>
                {/* X axis label */}
                <text x={width/2} y={height-2} fontSize={13} fill="#888" textAnchor="middle">Month</text>
                {/* Lines (smooth) */}
                {shownSeries.map((s, i) => (
                  <path key={s.label} d={smoothLinePath(s.data)} fill="none" stroke={s.color} strokeWidth={2.5} />
                ))}
                {/* Dots with white border */}
                {shownSeries.map((s, i) => s.data.map((v, j) => v === null ? null : (
                  <circle key={i+'-'+j} cx={x(j)} cy={y(v)} r={5} fill="#fff" stroke={s.color} strokeWidth={2.5} />
                )))}
              </svg>
              <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap', marginTop: 8, fontSize: 14, justifyContent: 'center' }}>
                <span style={{ fontWeight: 600, color: '#444', marginRight: 8 }}>Legend:</span>
                {shownSeries.map(s => (
                  <span key={s.label} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ width: 18, height: 3, background: s.color, display: 'inline-block', borderRadius: 2 }} />
                    {s.label}
                  </span>
                ))}
              </div>
            </div>
          </div>
        );
      })()}
      {/*Quarterly Revenue Cohorts Table */}
      {(() => {
        let cohortData = [];
        try { cohortData = JSON.parse(localStorage.getItem('cohortData')) || []; } catch { cohortData = []; }
        const numMonths = cohortData.length > 1 ? cohortData[1].revenue.length : 0;
        const maxQuarters = Math.ceil(numMonths / 3);
        // Build the monthly revenue table (integers)
        const revenueTable = cohortData.slice(1).map((cohort, cohortIdx) => {
          const numCols = numMonths;
          const trueCohortIdx = cohortIdx + 1;
          const enabledIndices = [];
          for (let i = 0; i < numCols; i++) {
            const enabled = i <= numCols - trueCohortIdx - 1 || trueCohortIdx + i === numCols - 1 || trueCohortIdx + i === numCols;
            if (enabled) enabledIndices.push(i);
          }
          return enabledIndices.map((monthIdx) => {
            const val = Array.isArray(cohort.revenue) && cohort.revenue[monthIdx] !== undefined ? parseFloat(cohort.revenue[monthIdx]) : 0;
            return isFinite(val) ? val : 0;
          });
        });
        // Build quarterly cohorts with the same logic as gross profit
        const quarterlyRows = [];
        for (let q = 0; q < Math.floor(revenueTable.length / 3); q++) {
          const cohortStart = q * 3;
          const cohortNames = cohortData.slice(1 + cohortStart, 1 + cohortStart + 3).map(c => c.name);
          const row = [];
          for (let quarter = 0; quarter < maxQuarters; quarter++) {
            let sum = 0;
            for (let i = 0; i < 3; i++) {
              const cohortIdx = cohortStart + i;
              if (!revenueTable[cohortIdx]) continue;
              if (quarter === 0) {
                for (let m = 0; m < 3 - i; m++) {
                  if (revenueTable[cohortIdx][m] !== undefined) {
                    sum += revenueTable[cohortIdx][m];
                  }
                }
              } else {
                const startMonth = quarter * 3 - i;
                for (let m = 0; m < 3; m++) {
                  const idx = startMonth + m;
                  if (idx >= 0 && revenueTable[cohortIdx][idx] !== undefined) {
                    sum += revenueTable[cohortIdx][idx];
                  }
                }
              }
            }
            row.push(sum);
          }
          quarterlyRows.push({ name: `${cohortNames[0]} - ${cohortNames[2]}`, values: row });
        }
        if (!quarterlyRows.length) return null;
        return (
          <div style={{ margin: '32px 0' }}>
            <h2>Quarterly Revenue Cohorts Table</h2>
            <table className="pl-table" style={{ width: 'auto', marginBottom: 0 }}>
              <thead>
                <tr>
                  <th>Quarterly Cohort</th>
                  {Array.from({ length: maxQuarters }, (_, i) => <th key={i}>Q{i + 1}</th>)}
                </tr>
              </thead>
              <tbody>
                {quarterlyRows.map((qr, idx) => (
                  <tr key={qr.name}>
                    <td style={{ fontWeight: 600 }}>{qr.name}</td>
                    {qr.values.map((v, i) => (
                      <td key={i} style={v === 0 ? { background: '#f3f3f3' } : {}}>{v !== 0 ? v.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }) : ''}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      })()}
      {/* 6. Quarterly Gross Profit Cohorts Table */}
      <h2 style={{ marginBottom: 18, marginTop: 48 }}>Quarterly Gross Profit Cohorts</h2>
      <table className="pl-table">
        <thead>
          <tr>
            <th>Quarterly Cohort</th>
            {(() => {
              let cohortData = [];
              let plData = [];
              try {
                cohortData = JSON.parse(localStorage.getItem('cohortData')) || [];
              } catch { cohortData = []; }
              try {
                plData = JSON.parse(localStorage.getItem('plData')) || [];
              } catch { plData = []; }
              const numMonths = cohortData.length > 1 ? cohortData[1].revenue.length : 0;
              const maxQuarters = Math.ceil(numMonths / 3);
              return Array.from({ length: maxQuarters }, (_, i) => <th key={i}>Q{i + 1}</th>);
            })()}
          </tr>
        </thead>
        <tbody>
          {(() => {
            let cohortData = [];
            let plData = [];
            try {
              cohortData = JSON.parse(localStorage.getItem('cohortData')) || [];
            } catch { cohortData = []; }
            try {
              plData = JSON.parse(localStorage.getItem('plData')) || [];
            } catch { plData = []; }
            const numMonths = cohortData.length > 1 ? cohortData[1].revenue.length : 0;
            const maxQuarters = Math.ceil(numMonths / 3);
            // Build the monthly gross profit table (integers)
            const grossProfitTable = cohortData.slice(1).map((cohort, cohortIdx) => {
              const numCols = numMonths;
              const trueCohortIdx = cohortIdx + 1;
              const enabledIndices = [];
              for (let i = 0; i < numCols; i++) {
                const enabled = i <= numCols - trueCohortIdx - 1 || trueCohortIdx + i === numCols - 1 || trueCohortIdx + i === numCols;
                if (enabled) enabledIndices.push(i);
              }
              const grossMargins = plData.map(row => {
                const revenue = parseFloat(row && row.revenue);
                const grossProfit = parseFloat(row && row.grossProfit);
                return (isFinite(revenue) && revenue !== 0 && isFinite(grossProfit)) ? (grossProfit / revenue) : null;
              });
              return enabledIndices.map((monthIdx, idxInEnabled) => {
                let grossMargin = null;
                const grossMarginIdx = grossMargins.length - enabledIndices.length + idxInEnabled;
                grossMargin = grossMargins[grossMarginIdx];
                const cohortRev = Array.isArray(cohort.revenue) && cohort.revenue[monthIdx] !== undefined ? parseFloat(cohort.revenue[monthIdx]) : NaN;
                if (grossMargin !== null && isFinite(cohortRev)) {
                  return Math.round(grossMargin * cohortRev);
                }
                return 0;
              });
            });
            // Build quarterly cohorts with corrected logic
            const quarterlyRows = [];
            for (let q = 0; q < Math.floor(grossProfitTable.length / 3); q++) {
              const cohortStart = q * 3;
              const cohortNames = cohortData.slice(1 + cohortStart, 1 + cohortStart + 3).map(c => c.name);
              const row = [];
              for (let quarter = 0; quarter < maxQuarters; quarter++) {
                let sum = 0;
                for (let i = 0; i < 3; i++) {
                  const cohortIdx = cohortStart + i;
                  if (!grossProfitTable[cohortIdx]) continue;
                  if (quarter === 0) {
                    // First column: 3 from first, 2 from second, 1 from third
                    for (let m = 0; m < 3 - i; m++) {
                      if (grossProfitTable[cohortIdx][m] !== undefined) {
                        sum += grossProfitTable[cohortIdx][m];
                      }
                    }
                  } else {
                    // Subsequent columns: sum 3 values per cohort, offset by quarter and cohort position
                    const startMonth = quarter * 3 - i;
                    for (let m = 0; m < 3; m++) {
                      const idx = startMonth + m;
                      if (idx >= 0 && grossProfitTable[cohortIdx][idx] !== undefined) {
                        sum += grossProfitTable[cohortIdx][idx];
                      }
                    }
                  }
                }
                row.push(sum);
              }
              quarterlyRows.push({ name: `${cohortNames[0]} - ${cohortNames[2]}`, values: row });
            }
            return quarterlyRows.map(qr => (
              <tr key={qr.name}>
                <td style={{ fontWeight: 600 }}>{qr.name}</td>
                {qr.values.map((v, i) => (
                  <td key={i} style={v === 0 ? { background: '#f3f3f3' } : {}}>{v !== 0 ? v : ''}</td>
                ))}
              </tr>
            ));
          })()}
        </tbody>
      </table>
      {/* Quarterly Gross Profit Cohorts Retention Table */}
      <h2 style={{ marginBottom: 18, marginTop: 48 }}>Quarterly Gross Profit Retention</h2>
      <table className="pl-table">
        <thead>
          <tr>
            <th>Quarterly Cohort</th>
            {(() => {
              let cohortData = [];
              try { cohortData = JSON.parse(localStorage.getItem('cohortData')) || []; } catch { cohortData = []; }
              const numMonths = cohortData.length > 1 ? cohortData[1].revenue.length : 0;
              const maxQuarters = Math.ceil(numMonths / 3);
              return Array.from({ length: maxQuarters }, (_, i) => <th key={i}>Q{i + 1}</th>);
            })()}
          </tr>
        </thead>
        <tbody>
          {(() => {
            let cohortData = [];
            let plData = [];
            try { cohortData = JSON.parse(localStorage.getItem('cohortData')) || []; } catch { cohortData = []; }
            try { plData = JSON.parse(localStorage.getItem('plData')) || []; } catch { plData = []; }
            const numMonths = cohortData.length > 1 ? cohortData[1].revenue.length : 0;
            const maxQuarters = Math.ceil(numMonths / 3);
            // Build the monthly gross profit table (integers)
            const grossProfitTable = cohortData.slice(1).map((cohort, cohortIdx) => {
              const numCols = numMonths;
              const trueCohortIdx = cohortIdx + 1;
              const enabledIndices = [];
              for (let i = 0; i < numCols; i++) {
                const enabled = i <= numCols - trueCohortIdx - 1 || trueCohortIdx + i === numCols - 1 || trueCohortIdx + i === numCols;
                if (enabled) enabledIndices.push(i);
              }
              const grossMargins = plData.map(row => {
                const revenue = parseFloat(row && row.revenue);
                const grossProfit = parseFloat(row && row.grossProfit);
                return (isFinite(revenue) && revenue !== 0 && isFinite(grossProfit)) ? (grossProfit / revenue) : null;
              });
              return enabledIndices.map((monthIdx, idxInEnabled) => {
                let grossMargin = null;
                const grossMarginIdx = grossMargins.length - enabledIndices.length + idxInEnabled;
                grossMargin = grossMargins[grossMarginIdx];
                const cohortRev = Array.isArray(cohort.revenue) && cohort.revenue[monthIdx] !== undefined ? parseFloat(cohort.revenue[monthIdx]) : NaN;
                if (grossMargin !== null && isFinite(cohortRev)) {
                  return Math.round(grossMargin * cohortRev);
                }
                return 0;
              });
            });
            // Build quarterly cohorts with corrected logic
            const quarterlyRows = [];
            for (let q = 0; q < Math.floor(grossProfitTable.length / 3); q++) {
              const cohortStart = q * 3;
              const cohortNames = cohortData.slice(1 + cohortStart, 1 + cohortStart + 3).map(c => c.name);
              const row = [];
              for (let quarter = 0; quarter < maxQuarters; quarter++) {
                let sum = 0;
                for (let i = 0; i < 3; i++) {
                  const cohortIdx = cohortStart + i;
                  if (!grossProfitTable[cohortIdx]) continue;
                  if (quarter === 0) {
                    for (let m = 0; m < 3 - i; m++) {
                      if (grossProfitTable[cohortIdx][m] !== undefined) {
                        sum += grossProfitTable[cohortIdx][m];
                      }
                    }
                  } else {
                    const startMonth = quarter * 3 - i;
                    for (let m = 0; m < 3; m++) {
                      const idx = startMonth + m;
                      if (idx >= 0 && grossProfitTable[cohortIdx][idx] !== undefined) {
                        sum += grossProfitTable[cohortIdx][idx];
                      }
                    }
                  }
                }
                row.push(sum);
              }
              quarterlyRows.push({ name: `${cohortNames[0]} - ${cohortNames[2]}`, values: row });
            }
            // Now, for each row, divide each cell by the Q2 value for that row
            return quarterlyRows.map(qr => {
              const q2 = qr.values[1];
              return (
                <tr key={qr.name}>
                  <td style={{ fontWeight: 600 }}>{qr.name}</td>
                  {qr.values.map((v, i) => {
                    let val = '';
                    if (i !== 1 && q2 && q2 !== 0 && v !== 0) {
                      val = ((v / q2) * 100).toFixed(1) + '%';
                    } else if (i === 1) {
                      val = '100.0%';
                    }
                    return <td key={i} style={v === 0 ? { background: '#f3f3f3' } : {}}>{v !== 0 ? val : ''}</td>;
                  })}
                </tr>
              );
            });
          })()}
        </tbody>
      </table>
      {/* 7. Quarterly Cohort Payback Table */}
      <h2 style={{ marginBottom: 18, marginTop: 48 }}>Quarterly Cohort Payback Table</h2>
      <table className="pl-table">
        <thead>
          <tr>
            <th>Quarterly Cohort</th>
            <th>S&M</th>
            {(() => {
              let cohortData = [];
              try {
                cohortData = JSON.parse(localStorage.getItem('cohortData')) || [];
              } catch { cohortData = []; }
              const numMonths = cohortData.length > 1 ? cohortData[1].revenue.length : 0;
              const maxQuarters = Math.ceil(numMonths / 3);
              return Array.from({ length: maxQuarters }, (_, i) => <th key={i}>Q{i + 1}</th>);
            })()}
          </tr>
        </thead>
        <tbody>
          {(() => {
            let cohortData = [];
            let plData = [];
            try {
              cohortData = JSON.parse(localStorage.getItem('cohortData')) || [];
            } catch { cohortData = []; }
            try {
              plData = JSON.parse(localStorage.getItem('plData')) || [];
            } catch { plData = []; }
            const numMonths = cohortData.length > 1 ? cohortData[1].revenue.length : 0;
            const maxQuarters = Math.ceil(numMonths / 3);
            // Build the quarterly gross profit table (integers, ignoring greyed out)
            const grossProfitTable = cohortData.slice(1).map((cohort, cohortIdx) => {
              const numCols = numMonths;
              const trueCohortIdx = cohortIdx + 1;
              const enabledIndices = [];
              for (let i = 0; i < numCols; i++) {
                const enabled = i <= numCols - trueCohortIdx - 1 || trueCohortIdx + i === numCols - 1 || trueCohortIdx + i === numCols;
                if (enabled) enabledIndices.push(i);
              }
              const grossMargins = plData.map(row => {
                const revenue = parseFloat(row && row.revenue);
                const grossProfit = parseFloat(row && row.grossProfit);
                return (isFinite(revenue) && revenue !== 0 && isFinite(grossProfit)) ? (grossProfit / revenue) : null;
              });
              return Array.from({ length: numCols }, (_, monthIdx) => {
                const idxInEnabled = enabledIndices.indexOf(monthIdx);
                if (idxInEnabled === -1) return 0;
                let grossMargin = null;
                const grossMarginIdx = grossMargins.length - enabledIndices.length + idxInEnabled;
                grossMargin = grossMargins[grossMarginIdx];
                const cohortRev = Array.isArray(cohort.revenue) && cohort.revenue[monthIdx] !== undefined ? parseFloat(cohort.revenue[monthIdx]) : NaN;
                if (grossMargin !== null && isFinite(cohortRev)) {
                  return Math.round(grossMargin * cohortRev);
                }
                return 0;
              });
            });
            // Build quarterly cohorts with corrected logic
            const quarterlyRows = [];
            for (let q = 0; q < Math.floor(grossProfitTable.length / 3); q++) {
              const cohortStart = q * 3;
              const cohortNames = cohortData.slice(1 + cohortStart, 1 + cohortStart + 3).map(c => c.name);
              // S&M for the quarterly cohort: sum of S&M for the 3 months
              let sm = 0;
              for (let i = 0; i < 3; i++) {
                const plIdx = cohortStart + i;
                if (plData[plIdx] && plData[plIdx].sm !== undefined && !isNaN(Number(plData[plIdx].sm))) {
                  sm += parseFloat(plData[plIdx].sm);
                }
              }
              const row = [];
              let cumulative = 0;
              for (let quarter = 0; quarter < maxQuarters; quarter++) {
                let sum = 0;
                for (let i = 0; i < 3; i++) {
                  const cohortIdx = cohortStart + i;
                  if (!grossProfitTable[cohortIdx]) continue;
                  if (quarter === 0) {
                    for (let m = 0; m < 3 - i; m++) {
                      if (grossProfitTable[cohortIdx][m] !== undefined) {
                        sum += grossProfitTable[cohortIdx][m];
                      }
                    }
                  } else {
                    const startMonth = quarter * 3 - i;
                    for (let m = 0; m < 3; m++) {
                      const idx = startMonth + m;
                      if (idx >= 0 && grossProfitTable[cohortIdx][idx] !== undefined) {
                        sum += grossProfitTable[cohortIdx][idx];
                      }
                    }
                  }
                }
                cumulative += sum;
                if (sm && sm !== 0) {
                  row.push((cumulative / sm).toFixed(2));
                } else {
                  row.push('');
                }
              }
              quarterlyRows.push({ name: `${cohortNames[0]} - ${cohortNames[2]}`, sm, values: row });
            }
            return quarterlyRows.map((qr, rowIdx) => (
              <tr key={qr.name}>
                <td style={{ fontWeight: 600 }}>{qr.name}</td>
                <td style={{ fontWeight: 600 }}>{qr.sm ? `$${Math.round(qr.sm).toLocaleString()}` : ''}</td>
                {qr.values.map((v, colIdx) => {
                  // Grey out if the corresponding cell in the gross profit table is 0 or if below the diagonal
                  const grossProfitVal = quarterlyRows[rowIdx] && quarterlyRows[rowIdx].values[colIdx] !== undefined ? quarterlyRows[rowIdx].values[colIdx] : undefined;
                  const numRows = quarterlyRows.length;
                  const isQ3orLater = colIdx >= 2;
                  const isBelowDiagonal = rowIdx + colIdx >= numRows + 1 && isQ3orLater;
                  const isGreyed = grossProfitVal === 0 || isBelowDiagonal;
                  // Highlight the leftmost value > 1 in the row (right of S&M)
                  let highlight = false;
                  if (!isGreyed && v !== '' && !isNaN(Number(v)) && Number(v) > 1) {
                    const firstIdx = qr.values.findIndex((val, idx) => idx >= 0 && val !== '' && !isNaN(Number(val)) && Number(val) > 1);
                    if (firstIdx === colIdx) highlight = true;
                  }
                  return <td key={colIdx} style={isGreyed ? { background: '#f3f3f3' } : highlight ? { background: '#ffe082' } : {}}>{isGreyed ? '' : v}</td>;
                })}
              </tr>
            ));
          })()}
        </tbody>
      </table>
      {/* 8. Quarterly Cohort Payback Chart */}
      {(() => {
        let cohortData = [];
        let plData = [];
        try {
          cohortData = JSON.parse(localStorage.getItem('cohortData')) || [];
        } catch { cohortData = []; }
        try {
          plData = JSON.parse(localStorage.getItem('plData')) || [];
        } catch { plData = []; }
        const numMonths = cohortData.length > 1 ? cohortData[1].revenue.length : 0;
        const maxQuarters = Math.ceil(numMonths / 3);
        // Build the quarterly gross profit table (integers, ignoring greyed out)
        const grossProfitTable = cohortData.slice(1).map((cohort, cohortIdx) => {
          const numCols = numMonths;
          const trueCohortIdx = cohortIdx + 1;
          const enabledIndices = [];
          for (let i = 0; i < numCols; i++) {
            const enabled = i <= numCols - trueCohortIdx - 1 || trueCohortIdx + i === numCols - 1 || trueCohortIdx + i === numCols;
            if (enabled) enabledIndices.push(i);
          }
          const grossMargins = plData.map(row => {
            const revenue = parseFloat(row && row.revenue);
            const grossProfit = parseFloat(row && row.grossProfit);
            return (isFinite(revenue) && revenue !== 0 && isFinite(grossProfit)) ? (grossProfit / revenue) : null;
          });
          return Array.from({ length: numCols }, (_, monthIdx) => {
            const idxInEnabled = enabledIndices.indexOf(monthIdx);
            if (idxInEnabled === -1) return 0;
            let grossMargin = null;
            const grossMarginIdx = grossMargins.length - enabledIndices.length + idxInEnabled;
            grossMargin = grossMargins[grossMarginIdx];
            const cohortRev = Array.isArray(cohort.revenue) && cohort.revenue[monthIdx] !== undefined ? parseFloat(cohort.revenue[monthIdx]) : NaN;
            if (grossMargin !== null && isFinite(cohortRev)) {
              return Math.round(grossMargin * cohortRev);
            }
            return 0;
          });
        });
        // Build quarterly payback values
        const quarterlyRows = [];
        for (let q = 0; q < Math.floor(grossProfitTable.length / 3); q++) {
          const cohortStart = q * 3;
          const cohortNames = cohortData.slice(1 + cohortStart, 1 + cohortStart + 3).map(c => c.name);
          // S&M for the quarterly cohort: sum of S&M for the 3 months
          let sm = 0;
          for (let i = 0; i < 3; i++) {
            const plIdx = cohortStart + i;
            if (plData[plIdx] && plData[plIdx].sm !== undefined && !isNaN(Number(plData[plIdx].sm))) {
              sm += parseFloat(plData[plIdx].sm);
            }
          }
          const row = [];
          let cumulative = 0;
          for (let quarter = 0; quarter < maxQuarters; quarter++) {
            let sum = 0;
            for (let i = 0; i < 3; i++) {
              const cohortIdx = cohortStart + i;
              if (!grossProfitTable[cohortIdx]) continue;
              if (quarter === 0) {
                for (let m = 0; m < 3 - i; m++) {
                  if (grossProfitTable[cohortIdx][m] !== undefined) {
                    sum += grossProfitTable[cohortIdx][m];
                  }
                }
              } else {
                const startMonth = quarter * 3 - i;
                for (let m = 0; m < 3; m++) {
                  const idx = startMonth + m;
                  if (idx >= 0 && grossProfitTable[cohortIdx][idx] !== undefined) {
                    sum += grossProfitTable[cohortIdx][idx];
                  }
                }
              }
            }
            cumulative += sum;
            if (sm && sm !== 0) {
              row.push((cumulative / sm).toFixed(2));
            } else {
              row.push('');
            }
          }
          quarterlyRows.push({ name: `${cohortNames[0]} - ${cohortNames[2]}`, sm, values: row });
        }
        // Prepare chart data (ignore greyed out/empty cells)
        const paybackSeries = quarterlyRows.map((qr, rowIdx) => {
          return {
            label: qr.name,
            color: [
              '#1976d2', '#43a047', '#ff9800', '#e53935', '#8e24aa', '#00897b', '#6d4c41', '#fbc02d', '#0080ff', '#444'
            ][rowIdx % 10],
            data: qr.values.map((v, colIdx) => {
              // Greyed out if value is empty or 0 or if the cell would be greyed out in the table
              const grossProfitVal = quarterlyRows[rowIdx] && quarterlyRows[rowIdx].values[colIdx] !== undefined ? quarterlyRows[rowIdx].values[colIdx] : undefined;
              const numRows = quarterlyRows.length;
              const isQ3orLater = colIdx >= 2;
              const isBelowDiagonal = rowIdx + colIdx >= numRows + 1 && isQ3orLater;
              const isGreyed = v === '' || v === 0 || isBelowDiagonal;
              return isGreyed ? null : parseFloat(v);
            })
          };
        });
        // State for toggling series
        const [enabled, setEnabled] = React.useState(() => paybackSeries.map(() => true));
        React.useEffect(() => {
          setEnabled(paybackSeries.map(() => true));
        }, [quarterlyRows.length]);
        const width = Math.max(60 * maxQuarters, 900);
        const height = 600;
        const shownSeries = paybackSeries.filter((_, i) => enabled[i]);
        const allVals = shownSeries.flatMap(s => s.data).filter(v => v !== null);
        const maxY = allVals.length > 0 ? Math.max(...allVals) : 1;
        const minY = allVals.length > 0 ? Math.min(...allVals) : 0;
        const x = idx => 40 + idx * (width - 60) / (maxQuarters - 1);
        const y = v => height - 30 - ((v - minY) / (maxY - minY || 1)) * (height - 60);
        function smoothLinePath(data) {
          let d = '';
          let last = null;
          for (let i = 0; i < data.length; i++) {
            const v = data[i];
            if (v === null) continue;
            const cx = x(i), cy = y(v);
            if (last === null) {
              d += `M ${cx} ${cy}`;
            } else {
              const prevX = x(last.i), prevY = y(last.v);
              const c1x = prevX + (cx - prevX) / 2;
              const c1y = prevY;
              const c2x = prevX + (cx - prevX) / 2;
              const c2y = cy;
              d += ` C ${c1x} ${c1y}, ${c2x} ${c2y}, ${cx} ${cy}`;
            }
            last = { i, v };
          }
          return d;
        }
        return (
          <div style={{ margin: '32px 0 0 0', width: '100%' }}>
            <div style={{ background: '#fff', border: '1px solid #eee', borderRadius: 12, boxShadow: '0 2px 12px #0001', padding: 16, position: 'relative', width: width }}>
              {/* Radio buttons for toggling curves */}
              <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap', marginBottom: 12, fontSize: 15, alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ fontWeight: 600, color: '#444', marginRight: 8 }}>Show cohorts:</span>
                {paybackSeries.map((s, i) => (
                  <label key={s.label} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={enabled[i]}
                      onChange={() => setEnabled(en => en.map((v, idx) => idx === i ? !v : v))}
                      style={{ accentColor: s.color, width: 16, height: 16 }}
                    />
                    <span style={{ width: 18, height: 3, background: s.color, display: 'inline-block', borderRadius: 2 }} />
                    {s.label}
                  </label>
                ))}
              </div>
              <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} style={{ display: 'block' }}>
                {/* Y axis grid and ticks */}
                {[minY, (minY+maxY)/2, maxY].map((tick, i) => (
                  <g key={i}>
                    <line x1={35} x2={width-15} y1={y(tick)} y2={y(tick)} stroke="#eee" />
                    <text x={10} y={y(tick)+4} fontSize={12} fill="#888">{tick.toFixed(1)}</text>
                  </g>
                ))}
                {/* X axis labels */}
                {Array.from({ length: maxQuarters }, (_, i) => (
                  <text key={i} x={x(i)} y={height-10} fontSize={12} fill="#888" textAnchor="middle">Q{i+1}</text>
                ))}
                {/* Y axis label */}
                <text x={-height/2} y={16} fontSize={13} fill="#888" textAnchor="middle" transform={`rotate(-90 16,${height/2})`}>Payback</text>
                {/* X axis label */}
                <text x={width/2} y={height-2} fontSize={13} fill="#888" textAnchor="middle">Quarter</text>
                {/* Lines (smooth) */}
                {shownSeries.map((s, i) => (
                  <path key={s.label} d={smoothLinePath(s.data)} fill="none" stroke={s.color} strokeWidth={2.5} />
                ))}
                {/* Dots with white border */}
                {shownSeries.map((s, i) => s.data.map((v, j) => v === null ? null : (
                  <circle key={i+'-'+j} cx={x(j)} cy={y(v)} r={5} fill="#fff" stroke={s.color} strokeWidth={2.5} />
                )))}
              </svg>
              <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap', marginTop: 8, fontSize: 14, justifyContent: 'center' }}>
                <span style={{ fontWeight: 600, color: '#444', marginRight: 8 }}>Legend:</span>
                {shownSeries.map(s => (
                  <span key={s.label} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ width: 18, height: 3, background: s.color, display: 'inline-block', borderRadius: 2 }} />
                    {s.label}
                  </span>
                ))}
              </div>
            </div>
          </div>
        );
      })()}
      {/* 9. Unit Economics Section */}
      <h2 style={{ marginBottom: 18 }}>S&M / New Revenue Analysis</h2>
      <table className="pl-table" style={{ marginBottom: 0 }}>
        <thead>
          <tr>
            <th></th>
            {monthLabels.map((m, idx) => <th key={idx}>{m.abbrev}</th>)}
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style={{ fontWeight: 600 }}>S&M</td>
            {(() => {
              let plData = [];
              try {
                plData = JSON.parse(localStorage.getItem('plData')) || [];
              } catch { plData = []; }
              // Each column: S&M for month idx from P&L
              return monthLabels.map((m, idx) => {
                const sm = plData[idx] && plData[idx].sm !== undefined ? plData[idx].sm : '';
                return <td key={idx}>{sm !== '' && !isNaN(Number(sm)) ? Number(sm).toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }) : ''}</td>;
              });
            })()}
          </tr>
          <tr>
            <td style={{ fontWeight: 600 }}>New Revenue</td>
            {(() => {
              let cohortData = [];
              try {
                cohortData = JSON.parse(localStorage.getItem('cohortData')) || [];
              } catch { cohortData = []; }
              // Each column: first column (index 0) of cohort idx+1 (skip 'Older Cohorts')
              return monthLabels.map((m, idx) => {
                const cohortRow = cohortData[idx+1];
                const val = cohortRow && Array.isArray(cohortRow.revenue) && cohortRow.revenue[0] !== undefined ? cohortRow.revenue[0] : '';
                return <td key={idx}>{val !== '' && !isNaN(Number(val)) ? Number(val).toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }) : ''}</td>;
              });
            })()}
          </tr>
          <tr>
            <td style={{ fontWeight: 600 }}>S&M/NewRev</td>
            {(() => {
              let plData = [];
              let cohortData = [];
              try {
                plData = JSON.parse(localStorage.getItem('plData')) || [];
              } catch { plData = []; }
              try {
                cohortData = JSON.parse(localStorage.getItem('cohortData')) || [];
              } catch { cohortData = []; }
              return monthLabels.map((m, idx) => {
                // First row value: S&M for month idx from P&L
                const sm = plData[idx] && plData[idx].sm !== undefined ? parseFloat(plData[idx].sm) : NaN;
                // Second row value: first column (index 0) of cohort idx+1
                const cohortRow = cohortData[idx+1];
                const denom = cohortRow && Array.isArray(cohortRow.revenue) && cohortRow.revenue[0] !== undefined ? parseFloat(cohortRow.revenue[0]) : NaN;
                let val = '';
                if (isFinite(sm) && isFinite(denom) && denom !== 0) {
                  val = Math.round(sm / denom);
                }
                return <td key={idx}>{val}</td>;
              });
            })()}
          </tr>
          <tr>
            <td style={{ fontWeight: 600 }}>Rolling Avg (3mo)</td>
            {(() => {
              let plData = [];
              let cohortData = [];
              try {
                plData = JSON.parse(localStorage.getItem('plData')) || [];
              } catch { plData = []; }
              try {
                cohortData = JSON.parse(localStorage.getItem('cohortData')) || [];
              } catch { cohortData = []; }
              return monthLabels.map((m, idx) => {
                if (idx < 2) return <td key={idx}></td>;
                // Sums for last 3 months
                let smSum = 0;
                let revSum = 0;
                for (let j = idx - 2; j <= idx; j++) {
                  const sm = plData[j] && plData[j].sm !== undefined ? parseFloat(plData[j].sm) : NaN;
                  const cohortRow = cohortData[j+1];
                  const rev = cohortRow && Array.isArray(cohortRow.revenue) && cohortRow.revenue[0] !== undefined ? parseFloat(cohortRow.revenue[0]) : NaN;
                  if (isFinite(sm)) smSum += sm;
                  if (isFinite(rev)) revSum += rev;
                }
                let val = '';
                if (revSum !== 0 && isFinite(smSum) && isFinite(revSum)) {
                  val = Math.round(smSum / revSum);
                }
                return <td key={idx}>{val}</td>;
              });
            })()}
          </tr>
        </tbody>
      </table>
      {/* Statistics Table for Unit Economics */}
      {(() => {
        let plData = [];
        let cohortData = [];
        try { plData = JSON.parse(localStorage.getItem('plData')) || []; } catch { plData = []; }
        try { cohortData = JSON.parse(localStorage.getItem('cohortData')) || []; } catch { cohortData = []; }
        // Extract S&M/NewRev values, then filter out values > 10000 before computing stats
        const smNewRevVals = monthLabels.map((m, idx) => {
          const sm = plData[idx] && plData[idx].sm !== undefined ? parseFloat(plData[idx].sm) : NaN;
          const cohortRow = cohortData[idx+1];
          const denom = cohortRow && Array.isArray(cohortRow.revenue) && cohortRow.revenue[0] !== undefined ? parseFloat(cohortRow.revenue[0]) : NaN;
          if (isFinite(sm) && isFinite(denom) && denom !== 0) {
            return sm / denom;
          }
          return null;
        }).filter(v => v !== null && isFinite(v) && v <= 10000);
        // Extract Rolling Avg (3mo) values
        const rollingAvgVals = monthLabels.map((m, idx) => {
          if (idx < 2) return null;
          let smSum = 0;
          let revSum = 0;
          for (let j = idx - 2; j <= idx; j++) {
            const sm = plData[j] && plData[j].sm !== undefined ? parseFloat(plData[j].sm) : NaN;
            const cohortRow = cohortData[j+1];
            const rev = cohortRow && Array.isArray(cohortRow.revenue) && cohortRow.revenue[0] !== undefined ? parseFloat(cohortRow.revenue[0]) : NaN;
            if (isFinite(sm)) smSum += sm;
            if (isFinite(rev)) revSum += rev;
          }
          if (revSum !== 0 && isFinite(smSum) && isFinite(revSum)) {
            return smSum / revSum;
          }
          return null;
        }).filter(v => v !== null && isFinite(v));
        // Helper to compute stats
        function getStats(arr) {
          if (!arr.length) return { min: '', max: '', mean: '', median: '', std: '' };
          const min = Math.min(...arr);
          const max = Math.max(...arr);
          const mean = arr.reduce((a, b) => a + b, 0) / arr.length;
          const sorted = [...arr].sort((a, b) => a - b);
          const median = sorted.length % 2 === 0
            ? (sorted[sorted.length/2 - 1] + sorted[sorted.length/2]) / 2
            : sorted[Math.floor(sorted.length/2)];
          const std = Math.sqrt(arr.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / arr.length);
          return { min, max, mean, median, std };
        }
        const stats1 = getStats(smNewRevVals);
        const stats2 = getStats(rollingAvgVals);
        // Extract S&M/NewRev values for each month
        const smNewRevRow = monthLabels.map((m, idx) => {
          const sm = plData[idx] && plData[idx].sm !== undefined ? parseFloat(plData[idx].sm) : NaN;
          const cohortRow = cohortData[idx+1];
          const denom = cohortRow && Array.isArray(cohortRow.revenue) && cohortRow.revenue[0] !== undefined ? parseFloat(cohortRow.revenue[0]) : NaN;
          if (isFinite(sm) && isFinite(denom) && denom !== 0) {
            return sm / denom;
          }
          return null;
        });
        // Count months with NO acquisition (blank, NaN, non-finite, or > 10000)
        const noAcqCount = smNewRevRow.filter(v => v === null || !isFinite(v) || v > 10000).length;
        const noAcqRatio = monthLabels.length ? Math.round((noAcqCount / monthLabels.length) * 100) + '%' : '';
        return (
          <div style={{ margin: '32px 0' }}>
            <h2>Statistics</h2>
            <table className="pl-table" style={{ width: 'auto', marginBottom: 0 }}>
              <thead>
                <tr>
                  <th></th>
                  <th>Min</th>
                  <th>Max</th>
                  <th>Mean</th>
                  <th>Median</th>
                  <th>Std Dev</th>
                  <th>No Acquisition Months</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>S&amp;M/NewRev</td>
                  <td>{stats1.min !== '' ? Math.round(stats1.min) : ''}</td>
                  <td>{stats1.max !== '' ? Math.round(stats1.max) : ''}</td>
                  <td>{stats1.mean !== '' ? Math.round(stats1.mean) : ''}</td>
                  <td>{stats1.median !== '' ? Math.round(stats1.median) : ''}</td>
                  <td>{stats1.std !== '' ? Math.round(stats1.std) : ''}</td>
                  <td>{noAcqRatio}</td>
                </tr>
                <tr>
                  <td>Rolling Avg (3mo)</td>
                  <td>{stats2.min !== '' ? Math.round(stats2.min) : ''}</td>
                  <td>{stats2.max !== '' ? Math.round(stats2.max) : ''}</td>
                  <td>{stats2.mean !== '' ? Math.round(stats2.mean) : ''}</td>
                  <td>{stats2.median !== '' ? Math.round(stats2.median) : ''}</td>
                  <td>{stats2.std !== '' ? Math.round(stats2.std) : ''}</td>
                  <td></td>
                </tr>
              </tbody>
            </table>
          </div>
        );
      })()}
      {/* Sophisticated Histogram for S&M/NewRev values < 10000 */}
      {(() => {
        try {
          let plData = [];
          let cohortData = [];
          try { plData = JSON.parse(localStorage.getItem('plData')) || []; } catch { plData = []; }
          try { cohortData = JSON.parse(localStorage.getItem('cohortData')) || []; } catch { cohortData = []; }
          const smNewRevVals = monthLabels.map((m, idx) => {
            const sm = plData[idx] && plData[idx].sm !== undefined ? parseFloat(plData[idx].sm) : NaN;
            const cohortRow = cohortData[idx+1];
            const denom = cohortRow && Array.isArray(cohortRow.revenue) && cohortRow.revenue[0] !== undefined ? parseFloat(cohortRow.revenue[0]) : NaN;
            if (isFinite(sm) && isFinite(denom) && denom !== 0) {
              return sm / denom;
            }
            return null;
          }).filter(v => v !== null && isFinite(v) && v < 10000);
          if (!smNewRevVals.length) return null;
          const numBins = 12;
          const min = Math.min(...smNewRevVals);
          const max = Math.max(...smNewRevVals);
          const binWidth = (max - min) / numBins || 1;
          const bins = Array(numBins).fill(0);
          smNewRevVals.forEach(v => {
            let binIdx = Math.floor((v - min) / binWidth);
            if (binIdx < 0) binIdx = 0;
            if (binIdx >= numBins) binIdx = numBins - 1;
            bins[binIdx]++;
          });
          const histHeight = 220;
          const histWidth = 700;
          const extraBottom = 60; // extra space for labels
          const maxCount = Math.max(...bins, 1);
          return (
            <div style={{ margin: '40px 0', background: '#fff', border: '1px solid #eee', borderRadius: 16, boxShadow: '0 2px 12px #0001', padding: 32, width: histWidth + 40, maxWidth: '100%', position: 'relative' }}>
              <h2 style={{ marginBottom: 18, fontSize: 28, color: '#1976d2', textAlign: 'center' }}>S&amp;M/NewRev Histogram</h2>
              <svg width={histWidth} height={histHeight + extraBottom + 60} style={{ display: 'block', margin: '0 auto' }}>
                {/* Y axis grid and ticks */}
                {[0, 0.25, 0.5, 0.75, 1].map((frac, i) => {
                  const tick = Math.round(maxCount * frac);
                  const y = histHeight - frac * histHeight + 40;
                  return (
                    <g key={i}>
                      <line x1={60} x2={histWidth-30} y1={y} y2={y} stroke="#e3eaf3" />
                      <text x={50} y={y+5} fontSize={16} fill="#888" textAnchor="end">{tick}</text>
                    </g>
                  );
                })}
                {/* Bars with blue gradient */}
                <defs>
                  <linearGradient id="histBarBlue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#1976d2" stopOpacity="0.85" />
                    <stop offset="100%" stopColor="#1976d2" stopOpacity="0.45" />
                  </linearGradient>
                </defs>
                {bins.map((count, i) => {
                  const x = 60 + i * ((histWidth - 90) / numBins);
                  const y = histHeight - (count / maxCount) * histHeight + 40;
                  const barWidth = ((histWidth - 90) / numBins) - 6;
                  const barHeight = (count / maxCount) * histHeight;
                  return (
                    <rect key={i} x={x} y={y} width={barWidth} height={barHeight} fill="url(#histBarBlue)" rx={4} />
                  );
                })}
                {/* X axis labels */}
                {bins.map((_, i) => {
                  if (numBins > 8 && i % 2 !== 0 && i !== 0 && i !== numBins - 1) return null;
                  const x = 60 + i * ((histWidth - 90) / numBins) + (((histWidth - 90) / numBins) / 2);
                  const binStart = (min + i * binWidth).toFixed(0);
                  const binEnd = (min + (i + 1) * binWidth).toFixed(0);
                  return (
                    <text
                      key={i}
                      x={x}
                      y={histHeight + extraBottom + 10}
                      fontSize={15}
                      fill="#888"
                      textAnchor="end"
                      transform={`rotate(-35 ${x},${histHeight + extraBottom + 10})`}
                    >
                      {binStart}-{binEnd}
                    </text>
                  );
                })}
                {/* Axis labels */}
                <text x={histWidth/2} y={histHeight + extraBottom + 60} fontSize={18} fill="#1976d2" textAnchor="middle">S&amp;M/NewRev Value</text>
                <text x={30} y={histHeight/2 + 40} fontSize={18} fill="#1976d2" textAnchor="middle" transform={`rotate(-90 30,${histHeight/2 + 40})`}>Count</text>
              </svg>
            </div>
          );
        } catch (e) { return null; }
      })()}
      
      {/* Sophisticated Histogram for Rolling Avg (3mo) values */}
      {(() => {
        try {
          let plData = [];
          let cohortData = [];
          try { plData = JSON.parse(localStorage.getItem('plData')) || []; } catch { plData = []; }
          try { cohortData = JSON.parse(localStorage.getItem('cohortData')) || []; } catch { cohortData = []; }
          const rollingAvgVals = monthLabels.map((m, idx) => {
            if (idx < 2) return null;
            let smSum = 0;
            let revSum = 0;
            for (let j = idx - 2; j <= idx; j++) {
              const sm = plData[j] && plData[j].sm !== undefined ? parseFloat(plData[j].sm) : NaN;
              const cohortRow = cohortData[j+1];
              const rev = cohortRow && Array.isArray(cohortRow.revenue) && cohortRow.revenue[0] !== undefined ? parseFloat(cohortRow.revenue[0]) : NaN;
              if (isFinite(sm)) smSum += sm;
              if (isFinite(rev)) revSum += rev;
            }
            if (revSum !== 0 && isFinite(smSum) && isFinite(revSum)) {
              return smSum / revSum;
            }
            return null;
          }).filter(v => v !== null && isFinite(v));
          if (!rollingAvgVals.length) return null;
          const numBins = 12;
          const min = Math.min(...rollingAvgVals);
          const max = Math.max(...rollingAvgVals);
          const binWidth = (max - min) / numBins || 1;
          const bins = Array(numBins).fill(0);
          rollingAvgVals.forEach(v => {
            let binIdx = Math.floor((v - min) / binWidth);
            if (binIdx < 0) binIdx = 0;
            if (binIdx >= numBins) binIdx = numBins - 1;
            bins[binIdx]++;
          });
          const histHeight = 220;
          const histWidth = 700;
          const extraBottom = 60; // extra space for labels
          const maxCount = Math.max(...bins, 1);
          return (
            <div style={{ margin: '40px 0', background: '#fff', border: '1px solid #eee', borderRadius: 16, boxShadow: '0 2px 12px #0001', padding: 32, width: histWidth + 40, maxWidth: '100%', position: 'relative' }}>
              <h2 style={{ marginBottom: 18, fontSize: 28, color: '#43a047', textAlign: 'center' }}>Rolling Avg (3mo) Histogram</h2>
              <svg width={histWidth} height={histHeight + extraBottom + 60} style={{ display: 'block', margin: '0 auto' }}>
                {/* Y axis grid and ticks */}
                {[0, 0.25, 0.5, 0.75, 1].map((frac, i) => {
                  const tick = Math.round(maxCount * frac);
                  const y = histHeight - frac * histHeight + 40;
                  return (
                    <g key={i}>
                      <line x1={60} x2={histWidth-30} y1={y} y2={y} stroke="#e3eaf3" />
                      <text x={50} y={y+5} fontSize={16} fill="#888" textAnchor="end">{tick}</text>
                    </g>
                  );
                })}
                {/* Bars with green gradient */}
                <defs>
                  <linearGradient id="histBarGreen" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#43a047" stopOpacity="0.85" />
                    <stop offset="100%" stopColor="#43a047" stopOpacity="0.45" />
                  </linearGradient>
                </defs>
                {bins.map((count, i) => {
                  const x = 60 + i * ((histWidth - 90) / numBins);
                  const y = histHeight - (count / maxCount) * histHeight + 40;
                  const barWidth = ((histWidth - 90) / numBins) - 6;
                  const barHeight = (count / maxCount) * histHeight;
                  return (
                    <rect key={i} x={x} y={y} width={barWidth} height={barHeight} fill="url(#histBarGreen)" rx={4} />
                  );
                })}
                {/* X axis labels */}
                {bins.map((_, i) => {
                  if (numBins > 8 && i % 2 !== 0 && i !== 0 && i !== numBins - 1) return null;
                  const x = 60 + i * ((histWidth - 90) / numBins) + (((histWidth - 90) / numBins) / 2);
                  const binStart = (min + i * binWidth).toFixed(0);
                  const binEnd = (min + (i + 1) * binWidth).toFixed(0);
                  return (
                    <text
                      key={i}
                      x={x}
                      y={histHeight + extraBottom + 10}
                      fontSize={15}
                      fill="#888"
                      textAnchor="end"
                      transform={`rotate(-35 ${x},${histHeight + extraBottom + 10})`}
                    >
                      {binStart}-{binEnd}
                    </text>
                  );
                })}
                {/* Axis labels */}
                <text x={histWidth/2} y={histHeight + extraBottom + 60} fontSize={18} fill="#43a047" textAnchor="middle">Rolling Avg (3mo) Value</text>
                <text x={30} y={histHeight/2 + 40} fontSize={18} fill="#43a047" textAnchor="middle" transform={`rotate(-90 30,${histHeight/2 + 40})`}>Count</text>
              </svg>
            </div>
          );
        } catch (e) { return null; }
      })()}
      {/* Yearly & Marginal CAC Table */}
      {(() => {
        let plData = [];
        let cohortData = [];
        try { plData = JSON.parse(localStorage.getItem('plData')) || []; } catch { plData = []; }
        try { cohortData = JSON.parse(localStorage.getItem('cohortData')) || []; } catch { cohortData = []; }
        const periods = [];
        const n = monthLabels.length;
        const periodLength = 12;
        for (let end = n; end >= periodLength; end -= periodLength) {
          const start = end - periodLength;
          let smSum = 0;
          let revSum = 0;
          let valid = true;
          for (let i = start; i < end; i++) {
            const sm = plData[i] && plData[i].sm !== undefined ? parseFloat(plData[i].sm) : NaN;
            const cohortRow = cohortData[i+1];
            const rev = cohortRow && Array.isArray(cohortRow.revenue) && cohortRow.revenue[0] !== undefined ? parseFloat(cohortRow.revenue[0]) : NaN;
            if (!isFinite(sm) || !isFinite(rev)) {
              valid = false;
              break;
            }
            smSum += sm;
            revSum += rev;
          }
          if (!valid) continue;
          const periodLabel = `${monthLabels[start].abbrev} - ${monthLabels[end-1].abbrev}`;
          periods.push({
            period: periodLabel,
            sm: smSum,
            rev: revSum,
            ratio: revSum !== 0 ? (smSum / revSum).toFixed(2) : ''
          });
        }
        if (periods.length === 0) return null;
        return (
          <div style={{ margin: '32px 0' }}>
            <h2>Yearly CAC</h2>
            <table className="pl-table" style={{ width: 'auto', marginBottom: 0 }}>
              <thead>
                <tr>
                  <th>Period</th>
                  <th>S&amp;M</th>
                  <th>New Revenue</th>
                  <th>S&amp;M/New Revenue</th>
                </tr>
              </thead>
              <tbody>
                {periods.map((row, idx) => (
                  <tr key={idx}>
                    <td>{row.period}</td>
                    <td>{row.sm.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })}</td>
                    <td>{row.rev.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })}</td>
                    <td>{row.ratio}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      })()}
      {/* Marginal CACs Table */}
      {(() => {
        // Recompute the same periods array as in the Yearly & Marginal CAC table
        let plData = [];
        let cohortData = [];
        try { plData = JSON.parse(localStorage.getItem('plData')) || []; } catch { plData = []; }
        try { cohortData = JSON.parse(localStorage.getItem('cohortData')) || []; } catch { cohortData = []; }
        const periods = [];
        const n = monthLabels.length;
        const periodLength = 12;
        for (let end = n; end >= periodLength; end -= periodLength) {
          const start = end - periodLength;
          let smSum = 0;
          let revSum = 0;
          let valid = true;
          for (let i = start; i < end; i++) {
            const sm = plData[i] && plData[i].sm !== undefined ? parseFloat(plData[i].sm) : NaN;
            const cohortRow = cohortData[i+1];
            const rev = cohortRow && Array.isArray(cohortRow.revenue) && cohortRow.revenue[0] !== undefined ? parseFloat(cohortRow.revenue[0]) : NaN;
            if (!isFinite(sm) || !isFinite(rev)) {
              valid = false;
              break;
            }
            smSum += sm;
            revSum += rev;
          }
          if (!valid) continue;
          const periodLabel = `${monthLabels[start].abbrev} - ${monthLabels[end-1].abbrev}`;
          periods.push({
            period: periodLabel,
            sm: smSum,
            rev: revSum,
            ratio: revSum !== 0 ? (smSum / revSum).toFixed(2) : ''
          });
        }
        if (periods.length < 2) return null;
        const marginals = [];
        for (let i = 0; i < periods.length - 1; i++) {
          const sm = periods[i].sm - periods[i+1].sm;
          const rev = periods[i].rev - periods[i+1].rev;
          marginals.push({
            period: periods[i].period,
            sm: sm,
            rev: rev,
            ratio: (isFinite(sm) && isFinite(rev) && rev !== 0) ? (sm / rev).toFixed(2) : ''
          });
        }
        return (
          <div style={{ margin: '32px 0' }}>
            <h2>Marginal CACs</h2>
            <table className="pl-table" style={{ width: 'auto', marginBottom: 0 }}>
              <thead>
                <tr>
                  <th>Marginal Period</th>
                  <th>S&amp;M</th>
                  <th>New Revenue</th>
                  <th>S&amp;M/New Revenue</th>
                </tr>
              </thead>
              <tbody>
                {marginals.map((row, idx) => (
                  <tr key={idx}>
                    <td>{row.period}</td>
                    <td>{row.sm.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })}</td>
                    <td>{row.rev.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })}</td>
                    <td>{row.ratio}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      })()}
      
      {/* EBITDA Margin Chart */}
      <h2 style={{ marginBottom: '18px', marginTop: '48px' }}>EBITCAC Evolution</h2>
      <EBITDAMarginChart />

      {/* After the NDR table rendering, add the following explanatory note: */}
      <div style={{ maxWidth: 900, margin: '24px auto 0 auto', fontSize: 15, color: '#444', background: '#f7f7fa', borderRadius: 8, padding: '16px 24px', border: '1px solid #e0e0e0', textAlign: 'left' }}>
        <strong>Notes:</strong>
        <ul style={{ margin: 0, paddingLeft: 24 }}>
          <li>The <strong>Forecast Curve</strong> is calculated using the weighted average retention of the last 12 months of available data in every column.</li>
          <li>The <strong>Conservative Forecast</strong> is calculated as the minimum of the median, simple avg, weighted avg, yearly weighted avgs, and forecast curve for every column, and only computes if at least 4 of the above are available.</li>
          <li>The S&M / New Rev statistics calculations exclude months in which there is no acquisition..</li>
        </ul>
      </div>
      </div>
  );
}

export default App;
