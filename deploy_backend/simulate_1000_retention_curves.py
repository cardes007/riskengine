import json
import random
from datetime import datetime
from simulate_retention_curve import get_retention_table, get_min_ndr_12th_root

def simulate_1000_retention_curves(conservative=True):
    retention_table, num_cols = get_retention_table()
    min_ndr_12th_root = get_min_ndr_12th_root()
    
    print("🎲 SIMULATING 1,000 RETENTION CURVES")
    print("=" * 60)
    print(f"12th root of min NDR: {min_ndr_12th_root:.4f} ({min_ndr_12th_root:.2%})")
    print(f"Note: 'Older Cohorts' row excluded from column-specific sampling")
    print(f"Conservative mode: {conservative}")
    
    # Analyze which columns have sufficient data (excluding first row)
    column_analysis = []
    for col in range(60):
        # Only count rows 2 onwards (exclude "Older Cohorts")
        col_values = [row[col] for row in retention_table[1:] if col < len(row) and row[col] is not None]
        has_sufficient_data = len(col_values) >= 12
        column_analysis.append((col, len(col_values), has_sufficient_data))
    
    print(f"\n📊 COLUMN DATA ANALYSIS (excluding 'Older Cohorts'):")
    print("Month | Valid Values | Has 12+ Values | Methodology")
    print("-" * 50)
    for col, count, sufficient in column_analysis:
        methodology = "Column-specific" if sufficient else "Global pool"
        print(f"M{col+1:2d}   | {count:11d} | {str(sufficient):13s} | {methodology}")
    
    # Find the transition point
    transition_month = None
    for col, count, sufficient in column_analysis:
        if not sufficient:
            transition_month = col + 1
            break
    
    if transition_month:
        print(f"\n🔄 METHODOLOGY TRANSITION:")
        print(f"Switches from column-specific to global pool at Month {transition_month}")
        print(f"Months 1-{transition_month-1}: Use column-specific values (if ≥12 available, excluding 'Older Cohorts')")
        print(f"Months {transition_month}-60: Use global pool (all non-None values including 'Older Cohorts')")
    else:
        print(f"\n✅ All 60 months have sufficient data for column-specific sampling")
    
    # Simulate 1,000 curves
    print(f"\n🔄 Running 1,000 simulations...")
    all_curves = []
    
    for sim in range(1000):
        if (sim + 1) % 100 == 0:
            print(f"  Completed {sim + 1:,}/1,000 simulations...")
        
        simulated_curve = []
        for col in range(60):
            # Gather all non-None values in this column (excluding "Older Cohorts" for column-specific)
            col_values = [row[col] for row in retention_table[1:] if col < len(row) and row[col] is not None]
            
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
                chosen = random.choice(all_values) if all_values else None
            
            if conservative and chosen is not None and chosen > max(1, min_ndr_12th_root):
                chosen = (max(1, min_ndr_12th_root) + chosen) / 2
            
            simulated_curve.append(chosen)
        
        all_curves.append(simulated_curve)
    
    print(f"\n✅ Simulation complete!")
    print(f"Generated {len(all_curves):,} retention curves")
    print(f"Each curve has {len(all_curves[0])} months")
    
    # Calculate some statistics
    print(f"\n📈 SIMULATION STATISTICS:")
    print(f"Total retention values generated: {len(all_curves) * len(all_curves[0]):,}")
    
    # Show a few sample curves
    print(f"\n📋 SAMPLE CURVES (first 5):")
    for i in range(min(5, len(all_curves))):
        print(f"Curve {i+1}: {[f'{x:.3f}' if x is not None else 'None' for x in all_curves[i][:10]]}...")
    
    print(f"\nData exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    return all_curves, transition_month

if __name__ == "__main__":
    simulate_1000_retention_curves(conservative=True) 