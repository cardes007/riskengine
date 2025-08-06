import pandas as pd
import numpy as np

def debug_excel_values():
    """Debug the actual values being read from the Excel file"""
    
    print("🔍 DEBUGGING EXCEL VALUES")
    print("=" * 60)
    
    # Try to read the conservative gross profit file
    try:
        df = pd.read_excel("gross_profit_simulation_conservative_20250731_214310.xlsx", sheet_name='Gross_Profit_Simulation')
        print(f"✅ Loaded {len(df)} rows from conservative gross profit simulation")
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return
    
    # Check the first row
    first_row = df.iloc[0]
    print(f"\nFirst row SM_Value: {first_row['SM_Value']}")
    
    # Check gross profit values for months 8-15
    print(f"\nGross profit values for months 8-15:")
    for month in range(8, 16):
        col_name = f'Gross_Profit_Month_{month}'
        value = first_row[col_name]
        print(f"  {col_name}: {value} (type: {type(value)}, pd.isna: {pd.isna(value)}, == 0: {value == 0})")
    
    # Check if there are any non-zero values after month 9
    print(f"\nChecking for non-zero values after month 9:")
    found_non_zero = False
    for month in range(10, 61):
        col_name = f'Gross_Profit_Month_{month}'
        value = first_row[col_name]
        if value != 0 and not pd.isna(value):
            print(f"  {col_name}: {value} (NON-ZERO!)")
            found_non_zero = True
    
    if not found_non_zero:
        print("  All values from month 10 onwards are 0 or NaN")
    
    # Test the transform logic with actual data
    print(f"\n" + "=" * 60)
    print("TESTING TRANSFORM LOGIC WITH ACTUAL DATA")
    print("=" * 60)
    
    sm_value = abs(first_row['SM_Value'])
    gross_profit_cashflows = [-sm_value]
    
    print("Building cash flows from actual data:")
    for month in range(1, 16):
        col_name = f'Gross_Profit_Month_{month}'
        value = first_row[col_name]
        
        if pd.isna(value):
            gross_profit_cashflows.append(0)
            print(f"  Month {month}: 0 (NaN)")
        elif value == 0:
            gross_profit_cashflows.append(0)
            print(f"  Month {month}: 0 (explicit 0)")
        else:
            gross_profit_cashflows.append(value)
            print(f"  Month {month}: {value}")
    
    print(f"\nCash flows (first 15): {gross_profit_cashflows[:15]}")
    
    # Test with lender cash flow calculator
    from lender_cashflow_calculator import calculate_lender_cashflows
    
    try:
        lender_cf, info = calculate_lender_cashflows(gross_profit_cashflows)
        print(f"\nLender cash flows (months 10-15): {lender_cf[10:15]}")
        print(f"Net return: ${info['net_return']:.2f}")
        
        # Check if there are any non-zero values after month 9
        print(f"\nChecking lender cash flows for non-zero values after month 9:")
        found_non_zero = False
        for month in range(10, min(16, len(lender_cf))):
            value = lender_cf[month]
            if value != 0:
                print(f"  Month {month}: {value} (NON-ZERO!)")
                found_non_zero = True
        
        if not found_non_zero:
            print("  All lender cash flows from month 10 onwards are 0")
            
    except Exception as e:
        print(f"Error calculating lender cash flows: {e}")

if __name__ == "__main__":
    debug_excel_values() 