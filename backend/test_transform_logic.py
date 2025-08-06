import pandas as pd
import numpy as np

def test_transform_logic():
    """Test the transform logic to identify the issue with zero values"""
    
    print("🧪 TESTING TRANSFORM LOGIC")
    print("=" * 60)
    
    # Create a sample row with zeros from month 10 onwards
    sample_row = {
        'SM_Value': -1000,
        'Gross_Profit_Month_1': 100,
        'Gross_Profit_Month_2': 80,
        'Gross_Profit_Month_3': 60,
        'Gross_Profit_Month_4': 40,
        'Gross_Profit_Month_5': 20,
        'Gross_Profit_Month_6': 10,
        'Gross_Profit_Month_7': 5,
        'Gross_Profit_Month_8': 2,
        'Gross_Profit_Month_9': 1,
        'Gross_Profit_Month_10': 0,  # Zero from here onwards
        'Gross_Profit_Month_11': 0,
        'Gross_Profit_Month_12': 0,
        'LTV_to_CAC': 0.5,
        'IRR': 0.1
    }
    
    # Fill in remaining months with zeros
    for month in range(13, 61):
        sample_row[f'Gross_Profit_Month_{month}'] = 0
    
    print("Sample row data:")
    print(f"SM_Value: {sample_row['SM_Value']}")
    for month in range(1, 16):  # Show first 15 months
        col_name = f'Gross_Profit_Month_{month}'
        print(f"{col_name}: {sample_row[col_name]}")
    print("... (remaining months are 0)")
    
    # Test the current logic
    print("\n" + "=" * 60)
    print("TESTING CURRENT LOGIC")
    print("=" * 60)
    
    sm_value = abs(sample_row['SM_Value'])
    gross_profit_cashflows = [-sm_value]
    
    print("Current logic results:")
    for month in range(1, 16):
        col_name = f'Gross_Profit_Month_{month}'
        if col_name in sample_row and pd.notna(sample_row[col_name]):
            value = sample_row[col_name]
            gross_profit_cashflows.append(value)
            print(f"Month {month}: {value} (pd.notna: {pd.notna(sample_row[col_name])})")
        else:
            gross_profit_cashflows.append(0)
            print(f"Month {month}: 0 (pd.notna: {pd.notna(sample_row[col_name])})")
    
    print(f"\nGross profit cash flows (first 15): {gross_profit_cashflows[:15]}")
    
    # Test the correct logic
    print("\n" + "=" * 60)
    print("TESTING CORRECT LOGIC")
    print("=" * 60)
    
    correct_cashflows = [-sm_value]
    
    print("Correct logic results:")
    for month in range(1, 16):
        col_name = f'Gross_Profit_Month_{month}'
        if col_name in sample_row and pd.notna(sample_row[col_name]) and sample_row[col_name] != 0:
            value = sample_row[col_name]
            correct_cashflows.append(value)
            print(f"Month {month}: {value} (not None and not 0)")
        else:
            correct_cashflows.append(0)
            print(f"Month {month}: 0 (None or 0)")
    
    print(f"\nCorrect cash flows (first 15): {correct_cashflows[:15]}")
    
    # Test with the lender cash flow calculator
    print("\n" + "=" * 60)
    print("TESTING WITH LENDER CASH FLOW CALCULATOR")
    print("=" * 60)
    
    from lender_cashflow_calculator import calculate_lender_cashflows
    
    # Test current logic
    try:
        lender_cf_current, info_current = calculate_lender_cashflows(gross_profit_cashflows)
        print(f"Current logic - Lender cash flows (months 10-15): {lender_cf_current[10:15]}")
        print(f"Current logic - Net return: ${info_current['net_return']:.2f}")
    except Exception as e:
        print(f"Current logic error: {e}")
    
    # Test correct logic
    try:
        lender_cf_correct, info_correct = calculate_lender_cashflows(correct_cashflows)
        print(f"Correct logic - Lender cash flows (months 10-15): {lender_cf_correct[10:15]}")
        print(f"Correct logic - Net return: ${info_correct['net_return']:.2f}")
    except Exception as e:
        print(f"Correct logic error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ CONCLUSION")
    print("=" * 60)
    print("The issue is that the current logic treats 0 values as valid cash flows")
    print("When gross profit is 0, it should be treated as 0 in the lender calculation")
    print("The fix is to add an additional check: `and sample_row[col_name] != 0`")

if __name__ == "__main__":
    test_transform_logic() 