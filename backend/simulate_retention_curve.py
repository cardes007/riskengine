import json
import random
from datetime import datetime
from numpy import mean
import pandas as pd

# Helper to get the retention table as a 2D array
def get_retention_table(export_to_excel=False, excel_filename=None):
    with open('full_cohort_data.json', 'r') as f:
        cohorts_data = json.load(f)
    num_months = len(cohorts_data[0]['revenue_array'])
    num_cols = num_months - 1
    retention_table = []  # rows: cohorts, cols: months-1
    for i, cohort in enumerate(cohorts_data):
        row = []
        rev = cohort['revenue_array']
        for j in range(1, len(rev)):
            left = rev[j-1]
            curr = rev[j]
            if left not in [None, 0, ''] and curr not in [None, '']:
                row.append(curr / left)
            else:
                row.append(None)
        # Enforce max values per row: first 2 rows full, 3rd row max num_cols-1, 4th row max num_cols-2, etc.
        max_len = max(num_cols - (i - 1), 0) if i >= 2 else num_cols
        if len(row) > max_len:
            row = row[:max_len]
        retention_table.append(row)
    # Remove the last row
    retention_table = retention_table[:-1]
    cohorts_data = cohorts_data[:-1]
    
    if export_to_excel:
        df = pd.DataFrame(retention_table)
        df.index = [cohort['cohort_name'] if 'cohort_name' in cohort else f'Cohort {i+1}' for i, cohort in enumerate(cohorts_data)]
        df.columns = [f'Month_{i+1}' for i in range(num_cols)]
        if not excel_filename:
            excel_filename = f'retention_table_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        df.to_excel(excel_filename)
        print(f"Retention table exported to Excel: {excel_filename}")
    
    return retention_table, num_cols

def get_min_ndr_12th_root():
    # Reuse logic from calculate_ndr.py
    with open('full_cohort_data.json', 'r') as f:
        cohorts_data = json.load(f)
    num_months = len(cohorts_data[0]['revenue_array'])
    ndr_values = []
    for end_col in range(num_months-1, 11, -1):
        numerator = 0.0
        denominator = 0.0
        row = 0
        col = end_col
        cohort = cohorts_data[row]
        revenue_array = cohort['revenue_array']
        retained_value = revenue_array[col]
        numerator += retained_value
        base_col = col - 12
        base_value = revenue_array[base_col]
        denominator += base_value
        row = 1
        col = end_col
        if row < len(cohorts_data):
            cohort = cohorts_data[row]
            revenue_array = cohort['revenue_array']
            retained_value = revenue_array[col]
            numerator += retained_value
            base_col = col - 12
            base_value = revenue_array[base_col]
            denominator += base_value
        row = 2
        col = end_col - 1
        while row < len(cohorts_data) and col >= 12:
            cohort = cohorts_data[row]
            revenue_array = cohort['revenue_array']
            retained_value = revenue_array[col]
            numerator += retained_value
            base_col = col - 12
            base_value = revenue_array[base_col]
            denominator += base_value
            row += 1
            col -= 1
        ndr = numerator / denominator if denominator > 0 else None
        if ndr is not None:
            ndr_values.append(ndr)
    
    if not ndr_values:
        print("Warning: No valid NDR values found. Using default value of 1.0")
        return 1.0
    
    min_ndr = min(ndr_values)
    return min_ndr ** (1/12)

def simulate_retention_curve(conservative=True, export_pools_excel=True, excel_filename=None):
    retention_table, num_cols = get_retention_table()
    min_ndr_12th_root = get_min_ndr_12th_root()
    print(f"12th root of min NDR: {min_ndr_12th_root:.4f} ({min_ndr_12th_root:.2%})")
    print(f"Note: 'Older Cohorts' row excluded from column-specific sampling")
    print(f"Conservative mode: {conservative}")
    simulated_curve = []
    pool_records = []  # To store pools and chosen values for each month
    older_cohorts_row = retention_table[0] if len(retention_table) > 0 else []
    for col in range(60):
        col_values = [row[col] for row in retention_table[1:] if col < len(row) and row[col] is not None]
        pool = []
        if len(col_values) >= 12:
            # Find first non-empty column to the left
            left_col = None
            for c in range(col - 1, -1, -1):
                vals = [row[c] for row in retention_table[1:] if c < len(row) and row[c] is not None]
                if vals:
                    left_col = c
                    break
            # Find first non-empty column to the right
            right_col = None
            for c in range(col + 1, 60):
                vals = [row[c] for row in retention_table[1:] if c < len(row) and row[c] is not None]
                if vals:
                    right_col = c
                    break
            all_values = col_values.copy()
            if left_col is not None:
                left_values = [row[left_col] for row in retention_table[1:] if left_col < len(row) and row[left_col] is not None]
                all_values.extend(left_values)
            if right_col is not None:
                right_values = [row[right_col] for row in retention_table[1:] if right_col < len(row) and row[right_col] is not None]
                all_values.extend(right_values)
            pool = all_values
            chosen = random.choice(all_values)
        elif len(col_values) >= 5:
            # Find two non-empty columns to the left
            left_cols = []
            for c in range(col - 1, -1, -1):
                vals = [row[c] for row in retention_table[1:] if c < len(row) and row[c] is not None]
                if vals:
                    left_cols.append(c)
                    if len(left_cols) == 2:
                        break
            # Find two non-empty columns to the right
            right_cols = []
            for c in range(col + 1, 60):
                vals = [row[c] for row in retention_table[1:] if c < len(row) and row[c] is not None]
                if vals:
                    right_cols.append(c)
                    if len(right_cols) == 2:
                        break
            all_values = col_values.copy()
            for lc in left_cols:
                left_values = [row[lc] for row in retention_table[1:] if lc < len(row) and row[lc] is not None]
                all_values.extend(left_values)
            for rc in right_cols:
                right_values = [row[rc] for row in retention_table[1:] if rc < len(row) and row[rc] is not None]
                all_values.extend(right_values)
            pool = all_values
            chosen = random.choice(all_values) if all_values else None
        elif len(col_values) >= 2:
            # Find three non-empty columns to the left
            left_cols = []
            for c in range(col - 1, -1, -1):
                vals = [row[c] for row in retention_table[1:] if c < len(row) and row[c] is not None]
                if vals:
                    left_cols.append(c)
                    if len(left_cols) == 3:
                        break
            # Find three non-empty columns to the right
            right_cols = []
            for c in range(col + 1, 60):
                vals = [row[c] for row in retention_table[1:] if c < len(row) and row[c] is not None]
                if vals:
                    right_cols.append(c)
                    if len(right_cols) == 3:
                        break
            all_values = col_values.copy()
            for lc in left_cols:
                left_values = [row[lc] for row in retention_table[1:] if lc < len(row) and row[lc] is not None]
                all_values.extend(left_values)
            for rc in right_cols:
                right_values = [row[rc] for row in retention_table[1:] if rc < len(row) and row[rc] is not None]
                all_values.extend(right_values)
            pool = all_values
            chosen = random.choice(all_values) if all_values else None
        else:
            # Find five non-empty columns to the left
            left_cols = []
            for c in range(col - 1, -1, -1):
                vals = [row[c] for row in retention_table[1:] if c < len(row) and row[c] is not None]
                if vals:
                    left_cols.append(c)
                    if len(left_cols) == 5:
                        break
            # Find five non-empty columns to the right
            right_cols = []
            for c in range(col + 1, 60):
                vals = [row[c] for row in retention_table[1:] if c < len(row) and row[c] is not None]
                if vals:
                    right_cols.append(c)
                    if len(right_cols) == 5:
                        break
            all_values = col_values.copy()
            for lc in left_cols:
                left_values = [row[lc] for row in retention_table[1:] if lc < len(row) and row[lc] is not None]
                all_values.extend(left_values)
            for rc in right_cols:
                right_values = [row[rc] for row in retention_table[1:] if rc < len(row) and row[rc] is not None]
                all_values.extend(right_values)
            pool = all_values
            chosen = random.choice(all_values) if all_values else None
        if conservative and chosen is not None and chosen > max(1, min_ndr_12th_root):
            chosen = (max(1, min_ndr_12th_root)+chosen)/2
        simulated_curve.append(chosen)
        pool_records.append({
            'Month': col+1,
            'Chosen Value': chosen,
            'Pool Size': len(pool),
            'Pool Values': str(pool)
        })
    print("\nSimulated Retention Curve (60 months, None if not enough data):")
    print(simulated_curve)
    print(f"\nData exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if export_pools_excel:
        df = pd.DataFrame(pool_records)
        if not excel_filename:
            excel_filename = f'retention_curve_pools_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        df.to_excel(excel_filename, index=False)
        print(f"Pool details exported to Excel: {excel_filename}")

if __name__ == "__main__":
    simulate_retention_curve(conservative=True) 