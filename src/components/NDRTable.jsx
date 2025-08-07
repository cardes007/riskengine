import React, { useMemo } from 'react';

export default function NDRTable({ ndrTable, monthLabels, cohortData }) {
  // Memoize expensive calculations
  const { summary, yearlyRows, forecastCurve, minCurve } = useMemo(() => {
    if (!ndrTable || ndrTable.length === 0) {
      return { summary: { simple: [], weighted: [], median: [] }, yearlyRows: [], forecastCurve: [], minCurve: [] };
    }

    // Helper to compute simple and weighted averages for each NDR column
    function getNDRSummaryRows(ndrTable, cohortData, monthLabels) {
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

    const summary = getNDRSummaryRows(ndrTable, cohortData, monthLabels);
    const yearlyRows = getYearlyWeightedRows(cohortData, monthLabels);
    
    // Forecast Curve calculation
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

    return { summary, yearlyRows, forecastCurve, minCurve };
  }, [ndrTable, monthLabels, cohortData]);

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

  if (!ndrTable || ndrTable.length === 0) {
    return <div>No NDR data available</div>;
  }

  return (
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
  );
} 