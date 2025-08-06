import React, { useState, useEffect, useRef } from 'react';
import '../App.css';

const PL_LINES = [
  { key: 'revenue', label: 'Revenue', type: 'input', className: 'pl-main' },
  { key: 'cogs', label: 'COGS', type: 'input', className: 'pl-main' },
  { key: 'grossProfit', label: 'Gross Profit', type: 'input', className: 'pl-subtotal' },
  { key: 'opex', label: 'OPEX', type: 'input', className: 'pl-subtotal' },
  { key: 'sm', label: '   S&M', type: 'input', className: 'pl-sublabel' },
  { key: 'rd', label: '   R&D', type: 'input', className: 'pl-sublabel' },
  { key: 'ga', label: '   G&A', type: 'input', className: 'pl-sublabel' },
  { key: 'ebitda', label: 'EBITDA', type: 'input', className: 'pl-subtotal' },
  { key: 'taxes', label: 'Taxes', type: 'input', className: 'pl-main' },
  { key: 'interest', label: 'Interest', type: 'input', className: 'pl-main' },
  { key: 'da', label: 'D&A', type: 'input', className: 'pl-main' },
  { key: 'netIncome', label: 'Net Income', type: 'input', className: 'pl-total' },
];

const LOCAL_STORAGE_KEY = 'plData';
const ALL_MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

function getAbbrevMonthLabel(monthIdx, year) {
  const month = ALL_MONTHS[monthIdx].slice(0, 3);
  const yr = String(year).slice(-2);
  return `${month} ${yr}`;
}

function getDefaultPLRow(label) {
  return {
    month: label,
    revenue: '',
    cogs: '',
    grossProfit: '',
    opex: '',
    sm: '',
    rd: '',
    ga: '',
    ebitda: '',
    taxes: '',
    interest: '',
    da: '',
    netIncome: ''
  };
}

function mergePLData(monthLabels, prevData) {
  const prevMap = {};
  prevData.forEach(row => {
    prevMap[row.month] = row;
  });
  return monthLabels.map(m => {
    const prev = prevMap[m.label];
    if (!prev) return getDefaultPLRow(m.label);
    const merged = { ...getDefaultPLRow(m.label), ...prev, month: m.label };
    return merged;
  });
}

function validatePL(plData) {
  const errors = {};
  plData.forEach((row, monthIdx) => {
    const monthErrors = {};
    for (const line of PL_LINES) {
      if (line.type === 'input') {
        const val = row[line.key];
        if (val !== '' && isNaN(Number(val))) {
          monthErrors[line.key] = 'Must be a number';
        }
        // Only enforce non-negative for these lines:
        if ([
          'revenue', 'cogs', 'grossProfit', 'opex', 'sm', 'rd', 'ga', 'taxes', 'interest', 'da'
        ].includes(line.key) && val !== '' && Number(val) < 0) {
          monthErrors[line.key] = `${line.label.trim()} cannot be negative`;
        }
        // Allow negative for EBITDA and Net Income
      }
    }
    const revenue = parseFloat(row.revenue) || 0;
    const cogs = parseFloat(row.cogs) || 0;
    const grossProfit = parseFloat(row.grossProfit) || 0;
    const opex = parseFloat(row.opex) || 0;
    const sm = parseFloat(row.sm) || 0;
    const rd = parseFloat(row.rd) || 0;
    const ga = parseFloat(row.ga) || 0;
    const ebitda = parseFloat(row.ebitda) || 0;
    const taxes = parseFloat(row.taxes) || 0;
    const interest = parseFloat(row.interest) || 0;
    const da = parseFloat(row.da) || 0;
    const netIncome = parseFloat(row.netIncome) || 0;
    if (revenue !== 0 && cogs > revenue) {
      monthErrors['cogs'] = 'COGS cannot exceed Revenue';
    }
    if (revenue !== 0 && grossProfit > revenue) {
      monthErrors['grossProfit'] = 'Gross Profit cannot exceed Revenue';
    }
    if (
      row.grossProfit !== '' && row.revenue !== '' && row.cogs !== '' &&
      Math.abs(grossProfit - (revenue - cogs)) > 10
    ) {
      monthErrors['grossProfit'] = 'Gross Profit must equal Revenue - COGS (within $10 tolerance)';
    }
    if (
      row.opex !== '' && row.sm !== '' && row.rd !== '' && row.ga !== '' &&
      Math.abs(opex - (sm + rd + ga)) > 10
    ) {
      monthErrors['opex'] = 'OPEX must equal S&M + R&D + G&A (within $10 tolerance)';
    }
    if (
      row.ebitda !== '' && row.grossProfit !== '' && row.opex !== '' &&
      Math.abs(ebitda - (grossProfit - opex)) > 10
    ) {
      monthErrors['ebitda'] = 'EBITDA must equal Gross Profit - OPEX (within $10 tolerance)';
    }
    if (
      row.netIncome !== '' && row.ebitda !== '' && row.taxes !== '' && row.interest !== '' && row.da !== '' &&
      Math.abs(netIncome - (ebitda - taxes - interest - da)) > 10
    ) {
      monthErrors['netIncome'] = 'Net Income must equal EBITDA - Taxes - Interest - D&A (within $10 tolerance)';
    }
    errors[monthIdx] = monthErrors;
  });
  return errors;
}

export default function PLForm({ settings, setSettings, monthLabels }) {
  const [plData, setPLData] = useState(monthLabels.map(m => getDefaultPLRow(m.label)));
  const [errors, setErrors] = useState({});
  const [numMonthsInput, setNumMonthsInput] = useState(settings.numMonths.toString());
  const [undoStack, setUndoStack] = useState([]); // <-- Add undo stack
  const tableRef = useRef(null);
  const [rollingAvgVals, setRollingAvgVals] = useState([]);
  const [fitResult, setFitResult] = useState(null);
  const [fitError, setFitError] = useState(null);

  useEffect(() => {
    setNumMonthsInput(settings.numMonths.toString());
  }, [settings.numMonths]);

  useEffect(() => {
    // Load existing data from localStorage on mount
    const savedData = localStorage.getItem(LOCAL_STORAGE_KEY);
    if (savedData) {
      try {
        const parsedData = JSON.parse(savedData);
        console.log('Loading saved P&L data from localStorage:', parsedData);
        setPLData(prev => mergePLData(monthLabels, parsedData));
      } catch (error) {
        console.error('Error loading saved P&L data:', error);
        setPLData(prev => mergePLData(monthLabels, Array.isArray(prev) ? prev : []));
      }
    } else {
      setPLData(prev => mergePLData(monthLabels, Array.isArray(prev) ? prev : []));
    }
  }, [monthLabels]);

  useEffect(() => {
    // Always save to localStorage, even if there are validation errors
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(plData));
    console.log('P&L Data saved to localStorage:', plData);
    console.log('P&L Data length when saving:', plData?.length);
    console.log('P&L Data sample when saving:', plData?.slice(0, 2));
    setErrors(validatePL(plData));
  }, [plData]);

  const handleChange = (monthIdx, lineKey, value) => {
    // Remove commas and currency symbols before storing
    const cleaned = typeof value === 'string' ? value.replace(/[$,]/g, '').trim() : value;
    setPLData(prev => {
      setUndoStack(stack => [...stack, prev.map(row => ({ ...row }))]); // push previous state
      const updated = [...prev];
      if (!updated[monthIdx]) updated[monthIdx] = getDefaultPLRow(monthLabels[monthIdx]?.label || '');
      updated[monthIdx] = { ...updated[monthIdx], [lineKey]: cleaned };
      return updated;
    });
  };

  const handlePaste = (e) => {
    const clipboard = e.clipboardData.getData('text');
    const rows = clipboard.trim().split(/\r?\n/);
    // Only split columns on tabs, not commas
    const parsed = rows.map(row => row.split(/\t/));
    if (parsed.length === 0 || parsed[0].length === 0) return;
    const active = document.activeElement;
    if (!active || !active.dataset) return;
    const startRow = parseInt(active.dataset.row, 10);
    const startCol = parseInt(active.dataset.col, 10);
    if (isNaN(startRow) || isNaN(startCol)) return;
    setPLData(prev => {
      setUndoStack(stack => [...stack, prev.map(row => ({ ...row }))]); // push previous state
      const updated = prev.map(row => ({ ...row }));
      for (let r = 0; r < parsed.length; r++) {
        for (let c = 0; c < parsed[r].length; c++) {
          const rowIdx = startCol + c;
          const lineIdx = startRow + r;
          if (rowIdx < monthLabels.length && lineIdx < PL_LINES.length) {
            const line = PL_LINES[lineIdx];
            if (line.type === 'input') {
              if (!updated[rowIdx]) updated[rowIdx] = getDefaultPLRow(monthLabels[rowIdx]?.label || '');
              // Remove commas and currency symbols from pasted values
              let val = parsed[r][c].replace(/[$,]/g, '').trim();
              updated[rowIdx][line.key] = val;
            }
          }
        }
      }
      return updated;
    });
    e.preventDefault();
  };

  // Undo (Ctrl+Z/Cmd+Z) support
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
        setUndoStack(stack => {
          if (stack.length === 0) return stack;
          const prev = stack[stack.length - 1];
          setPLData(prev);
          return stack.slice(0, -1);
        });
        e.preventDefault();
      }
    };
    const table = tableRef.current;
    if (!table) return;
    table.addEventListener('keydown', handleKeyDown);
    return () => table.removeEventListener('keydown', handleKeyDown);
  }, []);

  useEffect(() => {
    const table = tableRef.current;
    if (!table) return;
    table.addEventListener('paste', handlePaste);
    return () => table.removeEventListener('paste', handlePaste);
  }, [plData, monthLabels]);

  // UI for settings
  const now = new Date();
  const currentMonthIdx = now.getMonth();
  const currentYear = now.getFullYear();
  const lastMonthOptions = [];
  for (let y = currentYear; y >= currentYear - 5; y--) {
    const maxMonth = y === currentYear ? currentMonthIdx - 1 : 11;
    for (let m = maxMonth; m >= 0; m--) {
      lastMonthOptions.push({
        value: `${m}-${y}`,
        label: getAbbrevMonthLabel(m, y)
      });
    }
  }

  const handleNumMonthsChange = (e) => {
    setNumMonthsInput(e.target.value);
    const val = e.target.value;
    if (/^\d+$/.test(val) && Number(val) >= 1) {
      setSettings(s => ({ ...s, numMonths: Number(val) }));
    }
  };
  const handleNumMonthsBlur = () => {
    let val = parseInt(numMonthsInput, 10);
    if (isNaN(val) || val < 1) val = 1;
    setSettings(s => ({ ...s, numMonths: val }));
    setNumMonthsInput(val.toString());
  };

  function computeRollingAvgVals() {
    let plData = [];
    let cohortData = [];
    try { plData = JSON.parse(localStorage.getItem('plData')) || []; } catch { plData = []; }
    try { cohortData = JSON.parse(localStorage.getItem('cohortData')) || []; } catch { cohortData = []; }
    return monthLabels.map((m, idx) => {
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
        return Math.round(smSum / revSum);
      }
      return null;
    }).filter(v => v !== null && isFinite(v));
  }

  return (
    <div>
      <h2>P&L Statement Input</h2>
      <form style={{ marginBottom: 24, display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}
        onSubmit={e => e.preventDefault()}>
        <label>
          Number of months:
          <input
            type="number"
            min={1}
            value={numMonthsInput}
            onChange={handleNumMonthsChange}
            onBlur={handleNumMonthsBlur}
            style={{ width: 60, marginLeft: 8 }}
          />
        </label>
        <label>
          Last month of data:
          <select
            value={`${settings.lastMonthIdx}-${settings.year}`}
            onChange={e => {
              const [m, y] = e.target.value.split('-');
              setSettings(s => ({ ...s, lastMonthIdx: Number(m), year: Number(y) }));
            }}
            style={{ marginLeft: 8 }}
          >
            {lastMonthOptions.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </label>
      </form>
      <table className="pl-table" ref={tableRef}>
        <thead>
          <tr>
            <th>P&L Line</th>
            {monthLabels.map(m => (
              <th key={m.label}>{m.abbrev}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {PL_LINES.map((line, lineIdx) => (
            <tr key={line.key} className={line.className || ''}>
              <td className={line.className || ''}>{line.label}</td>
              {monthLabels.map((m, monthIdx) => {
                const row = plData[monthIdx] || getDefaultPLRow(m.label);
                const error = errors[monthIdx]?.[line.key];
                if (line.type === 'input') {
                  return (
                    <td key={m.label} className={error ? 'error-cell' : ''}>
                      <input
                        type="text"
                        value={row[line.key] ?? ''}
                        onChange={e => handleChange(monthIdx, line.key, e.target.value)}
                        className={error ? 'error-input' : ''}
                        data-row={lineIdx}
                        data-col={monthIdx}
                        tabIndex={0}
                      />
                      {error && (
                        <div className="error-message">{error}</div>
                      )}
                    </td>
                  );
                } else {
                  return <td key={m.label}></td>;
                }
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <div style={{ fontSize: 13, color: '#888', marginTop: 8 }}>
        <span>Tip: You can copy a P&amp;L from Excel or Google Sheets and paste it directly into this table. Undo with Ctrl+Z or Cmd+Z.</span>
      </div>
      {fitError && (
        <div style={{ color: 'red', margin: '16px 0' }}>
          Error: {fitError}
        </div>
      )}

      {fitResult && (
        <div style={{ margin: '24px 0' }}>
          <h3>Best Fit Distribution</h3>
          <table className="pl-table" style={{ width: 'auto', marginBottom: 0 }}>
            <thead>
              <tr>
                <th>Distribution</th>
                <th>Parameters</th>
                <th>KS Statistic</th>
                <th>KS p-value</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>{fitResult.best_distribution}</td>
                <td>
                  {fitResult.params.map((p, i) => (
                    <span key={i}>{p.toFixed(4)}{i < fitResult.params.length - 1 ? ', ' : ''}</span>
                  ))}
                </td>
                <td>{fitResult.ks_statistic.toFixed(4)}</td>
                <td>{fitResult.ks_pvalue.toFixed(4)}</td>
              </tr>
            </tbody>
          </table>
          <h3 style={{ margin: '24px 0 8px 0' }}>Best Fit Plot</h3>
          <img
            src={`data:image/png;base64,${fitResult.plot_base64}`}
            alt="Best fit distribution"
            style={{ maxWidth: 500, border: '1px solid #ccc', borderRadius: 8 }}
          />
        </div>
      )}
    </div>
  );
} 