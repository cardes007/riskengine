import React, { useState, useEffect, useRef } from 'react';
import '../App.css';

const LOCAL_STORAGE_KEY = 'cohortData';

function mergeCohortData(monthLabels, prevData) {
  const prevMap = {};
  prevData.forEach(row => {
    prevMap[row.name] = row;
  });
  // Always add 'Older Cohorts' at the top
  const result = [];
  const prevOlder = prevMap['Older Cohorts'];
  let olderRevenue = [];
  if (prevOlder && Array.isArray(prevOlder.revenue)) {
    olderRevenue = prevOlder.revenue.slice(0, monthLabels.length);
    while (olderRevenue.length < monthLabels.length) olderRevenue.push('');
  } else {
    olderRevenue = monthLabels.map(() => '');
  }
  result.push({ name: 'Older Cohorts', revenue: olderRevenue });
  // Then add the rest
  monthLabels.forEach(m => {
    const prev = prevMap[m.abbrev];
    let revenue = [];
    if (prev && Array.isArray(prev.revenue)) {
      revenue = prev.revenue.slice(0, monthLabels.length);
      while (revenue.length < monthLabels.length) {
        revenue.push('');
      }
    } else {
      revenue = monthLabels.map(() => '');
    }
    result.push({ name: m.abbrev, revenue });
  });
  return result;
}

export default function CohortForm({ monthLabels }) {
  const [cohorts, setCohorts] = useState(() => {
    // Always add 'Older Cohorts' at the top
    const base = [
      { name: 'Older Cohorts', revenue: monthLabels.map(() => '') },
      ...monthLabels.map(m => ({ name: m.abbrev, revenue: monthLabels.map(() => '') }))
    ];
    return base;
  });
  const [undoStack, setUndoStack] = useState([]);
  const tableRef = useRef(null);

  useEffect(() => {
    setCohorts(prev => {
      const merged = mergeCohortData(monthLabels, Array.isArray(prev) ? prev : []);
      // Remove data from greyed out cells
      return merged.map((row, cohortIdx) => {
        if (!Array.isArray(row.revenue)) return row;
        const numCols = monthLabels.length;
        const newRevenue = row.revenue.map((val, monthIdx) => {
          const allowInput = monthIdx <= numCols - cohortIdx - 1 || cohortIdx + monthIdx === numCols - 1 || cohortIdx + monthIdx === numCols;
          return allowInput ? val : '';
        });
        return { ...row, revenue: newRevenue };
      });
    });
  }, [monthLabels]);

  useEffect(() => {
    if (cohorts.length > 0) {
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(cohorts));
    }
  }, [cohorts]);

  // Undo (Ctrl+Z/Cmd+Z) support
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
        setUndoStack(stack => {
          if (stack.length === 0) return stack;
          const prev = stack[stack.length - 1];
          setCohorts(prev);
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

  const handleRevenueChange = (cohortIdx, monthIdx, value) => {
    setCohorts(prev => {
      setUndoStack(stack => [...stack, prev.map(row => ({ ...row, revenue: [...row.revenue] }))]);
      const updated = [...prev];
      let revenue = Array.isArray(updated[cohortIdx]?.revenue)
        ? [...updated[cohortIdx].revenue]
        : monthLabels.map(() => '');
      while (revenue.length < monthLabels.length) revenue.push('');
      revenue[monthIdx] = value;
      updated[cohortIdx] = {
        ...updated[cohortIdx],
        revenue
      };
      return updated;
    });
  };

  // Paste handler for Excel/Sheets-style paste
  useEffect(() => {
    const handlePaste = (e) => {
      const clipboard = e.clipboardData.getData('text');
      const rows = clipboard.trim().split(/\r?\n/);
      // Only split columns on tabs, not commas
      const parsed = rows.map(row => row.split(/\t/));
      if (parsed.length === 0 || parsed[0].length === 0) return;
      // Find the first focused cell
      const active = document.activeElement;
      if (!active || !active.dataset) return;
      const startRow = parseInt(active.dataset.row, 10);
      const startCol = parseInt(active.dataset.col, 10);
      if (isNaN(startRow) || isNaN(startCol)) return;
      setCohorts(prev => {
        setUndoStack(stack => [...stack, prev.map(row => ({ ...row, revenue: [...row.revenue] }))]);
        const updated = prev.map(row => ({ ...row, revenue: [...row.revenue] }));
        const numCols = monthLabels.length;
        for (let r = 0; r < parsed.length; r++) {
          for (let c = 0; c < parsed[r].length; c++) {
            const rowIdx = startRow + r;
            const colIdx = startCol + c;
            // Only allow input if cell is non-greyed out (matches UI logic)
            const allowInput = colIdx <= numCols - rowIdx - 1 || rowIdx + colIdx === numCols - 1 || rowIdx + colIdx === numCols;
            if (rowIdx < updated.length && colIdx < numCols && allowInput) {
              let val = parsed[r][c].replace(/[$,]/g, '').trim();
              updated[rowIdx].revenue[colIdx] = val;
            }
          }
        }
        return updated;
      });
      e.preventDefault();
    };
    const table = tableRef.current;
    if (!table) return;
    table.addEventListener('paste', handlePaste);
    return () => table.removeEventListener('paste', handlePaste);
  }, [monthLabels]);

  return (
    <div>
              <h2>Revenue Cohorts Input</h2>
      {cohorts.length > 0 && (
        <table className="pl-table" ref={tableRef} tabIndex={0}>
          <thead>
            <tr>
              <th>Cohort</th>
              {monthLabels.map((_, idx) => <th key={idx}>{idx + 1}</th>)}
            </tr>
          </thead>
          <tbody>
            {cohorts.map((cohort, cohortIdx) => (
              <tr key={cohort.name}>
                <td style={{ fontWeight: cohortIdx === 0 ? 700 : 600 }}>{cohort.name}</td>
                {monthLabels.map((_, monthIdx) => {
                  const numCols = monthLabels.length;
                  const allowInput = monthIdx <= numCols - cohortIdx - 1 || cohortIdx + monthIdx === numCols - 1 || cohortIdx + monthIdx === numCols;
                  return (
                    <td key={monthIdx} style={!allowInput ? { background: '#f3f3f3' } : {}}>
                      <input
                        type="number"
                        value={Array.isArray(cohort.revenue) && cohort.revenue[monthIdx] !== undefined ? cohort.revenue[monthIdx] : ''}
                        onChange={e => handleRevenueChange(cohortIdx, monthIdx, e.target.value)}
                        data-row={cohortIdx}
                        data-col={monthIdx}
                        disabled={!allowInput}
                        style={!allowInput ? { background: '#f3f3f3', cursor: 'not-allowed' } : {}}
                        tabIndex={0}
                      />
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <div style={{ fontSize: 13, color: '#888', marginTop: 8 }}>
        <span>Tip: You can copy cohort data from Excel or Google Sheets and paste it directly into this table. Undo with Ctrl+Z or Cmd+Z.</span>
      </div>
    </div>
  );
} 