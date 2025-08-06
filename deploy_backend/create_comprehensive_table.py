import pandas as pd
import json
import statistics
from datetime import datetime
from monte_carlo_predicted_ratio import run_monte_carlo_predicted_ratio
from simulate_1000_retention_curves import simulate_1000_retention_curves
from prediction_engine import load_pl_data

def calculate_simple_irr_fallback(sm_value, gross_profit_columns):
    """
    Simple IRR calculation fallback for comprehensive table
    """
    if sm_value <= 0:
        return None
    
    total_return = sum([gp for gp in gross_profit_columns if gp is not None and gp > 0])
    if total_return <= 0:
        return None  # Negative IRR
    
    # Simple approximation: assume average time to receive returns
    weighted_months = sum(i * gp for i, gp in enumerate(gross_profit_columns) if gp is not None and gp > 0)
    avg_month = weighted_months / total_return if total_return > 0 else 0
    avg_years = avg_month / 12
    
    # Simple IRR approximation
    if avg_years > 0:
        return (total_return / sm_value) ** (1 / avg_years) - 1
    else:
        return None

def calculate_gross_margin():
    """
    Calculate the gross margin to use for gross profit projections.
    Returns the minimum of:
    1. Overall gross margin (all revenue - all cogs) / all revenue
    2. Last 12 months gross margin (last 12 months revenue - last 12 months cogs) / last 12 months revenue
    3. Median monthly gross margin over the entire data period
    """
    try:
        revenue_dict, cogs_dict, gross_margin_dict = load_pl_data()
        
        if not revenue_dict:
            print("Warning: No P&L data found. Using default gross margin of 70%.")
            return 0.70
        
        # Convert to lists and sort by month
        months = sorted(revenue_dict.keys())
        revenues = [revenue_dict[month] for month in months]
        cogs = [cogs_dict[month] for month in months]
        gross_margins = [gross_margin_dict[month] for month in months]
        
        # 1. Overall gross margin
        total_revenue = sum(revenues)
        total_cogs = sum(cogs)
        overall_gross_margin = (total_revenue - total_cogs) / total_revenue if total_revenue > 0 else 0
        
        # 2. Last 12 months gross margin
        last_12_revenues = revenues[-12:] if len(revenues) >= 12 else revenues
        last_12_cogs = cogs[-12:] if len(cogs) >= 12 else cogs
        last_12_total_revenue = sum(last_12_revenues)
        last_12_total_cogs = sum(last_12_cogs)
        last_12_gross_margin = (last_12_total_revenue - last_12_total_cogs) / last_12_total_revenue if last_12_total_revenue > 0 else 0
        
        # 3. Median monthly gross margin
        valid_gross_margins = [gm for gm in gross_margins if gm > 0]
        median_monthly_gross_margin = statistics.median(valid_gross_margins) / 100 if valid_gross_margins else 0
        
        # Convert percentages to decimals for comparison
        overall_gross_margin_decimal = overall_gross_margin
        last_12_gross_margin_decimal = last_12_gross_margin
        median_monthly_gross_margin_decimal = median_monthly_gross_margin
        
        # Find the minimum
        gross_margins_to_compare = [
            overall_gross_margin_decimal,
            last_12_gross_margin_decimal,
            median_monthly_gross_margin_decimal
        ]
        
        selected_gross_margin = min(gross_margins_to_compare)
        
        print(f"📊 Gross Margin Analysis:")
        print(f"  Overall gross margin: {overall_gross_margin:.1%}")
        print(f"  Last 12 months gross margin: {last_12_gross_margin:.1%}")
        print(f"  Median monthly gross margin: {median_monthly_gross_margin:.1%}")
        print(f"  Selected gross margin (minimum): {selected_gross_margin:.1%}")
        
        return selected_gross_margin
        
    except Exception as e:
        print(f"Warning: Error calculating gross margin: {e}. Using default gross margin of 70%.")
        return 0.70

def build_revenue_table(simulations, all_retention_curves, label):
    print(f"\n📊 Building {label} revenue table...")
    
    table_data = []
    for i in range(1000):  # Changed from 12000 to 1000
        if (i + 1) % 100 == 0:  # Changed from 1000 to 100 for more frequent updates
            print(f"  Processing row {i + 1:,}/1,000...")  # Updated message
        mc_data = simulations[i]
        sm_value = mc_data['sm_value']
        predicted_ratio = mc_data['predicted_ratio']
        sm_ratio = sm_value / predicted_ratio if predicted_ratio != 0 else None
        retention_curve = all_retention_curves[i]
        row_data = {
            'SM_Value': -sm_value if sm_value is not None else None
        }
        prev_revenue = sm_ratio
        row_data['Revenue_Month_1'] = prev_revenue
        revenue_columns = [prev_revenue]
        
        for month in range(1, 60):
            retention_value = retention_curve[month]
            if prev_revenue is not None and retention_value is not None:
                revenue = prev_revenue * retention_value
            else:
                revenue = None
            row_data[f'Revenue_Month_{month + 1}'] = revenue
            revenue_columns.append(revenue)
            prev_revenue = revenue
        if sm_value and sm_value != 0:
            ltv_cac = sum([r for r in revenue_columns if r is not None]) / sm_value
        else:
            ltv_cac = None
        row_data['LTV_to_CAC'] = ltv_cac
        table_data.append(row_data)
    
    # Note: No summary or NDR rows added - keeping only the original data rows
    
    df = pd.DataFrame(table_data)
    print(f"✅ {label} revenue table created: {df.shape[0]:,} rows x {df.shape[1]} columns")
    return df

def build_gross_profit_table(simulations, all_retention_curves, label):
    print(f"\n📊 Building {label} gross profit table...")
    
    # Calculate gross margin for gross profit projections
    gross_margin = calculate_gross_margin()
    
    table_data = []
    for i in range(1000):  # Changed from 12000 to 1000
        if (i + 1) % 100 == 0:  # Changed from 1000 to 100 for more frequent updates
            print(f"  Processing row {i + 1:,}/1,000...")  # Updated message
        mc_data = simulations[i]
        sm_value = mc_data['sm_value']
        predicted_ratio = mc_data['predicted_ratio']
        sm_ratio = sm_value / predicted_ratio if predicted_ratio != 0 else None
        retention_curve = all_retention_curves[i]
        row_data = {
            'SM_Value': -sm_value if sm_value is not None else None
        }
        prev_revenue = sm_ratio
        # Calculate gross profit for month 1
        row_data['Gross_Profit_Month_1'] = prev_revenue * gross_margin if prev_revenue is not None else None
        gross_profit_columns = [row_data['Gross_Profit_Month_1']]
        
        for month in range(1, 60):
            retention_value = retention_curve[month]
            if prev_revenue is not None and retention_value is not None:
                revenue = prev_revenue * retention_value
            else:
                revenue = None
            # Calculate gross profit for this month
            gross_profit = revenue * gross_margin if revenue is not None else None
            row_data[f'Gross_Profit_Month_{month + 1}'] = gross_profit
            gross_profit_columns.append(gross_profit)
            prev_revenue = revenue
        if sm_value and sm_value != 0:
            ltv_cac = sum([gp for gp in gross_profit_columns if gp is not None]) / sm_value
        else:
            ltv_cac = None
        row_data['LTV_to_CAC'] = ltv_cac
        
        # Calculate IRR for this row's cash flow
        # Cash flow: [-S&M_value, gross_profit_month_1, gross_profit_month_2, ...]
        cash_flow = [-sm_value] + [gp if gp is not None else 0 for gp in gross_profit_columns]
        
        try:
            import numpy as np
            from numpy_financial import irr
            
            # Filter out None values and ensure we have valid cash flows
            valid_cash_flow = [cf for cf in cash_flow if cf is not None]
            if len(valid_cash_flow) > 1 and valid_cash_flow[0] < 0:
                calculated_irr = irr(valid_cash_flow)
                if calculated_irr is not None and np.isfinite(calculated_irr):
                    row_irr = calculated_irr
                else:
                    row_irr = None
            else:
                row_irr = None
        except ImportError:
            # Fallback IRR calculation if numpy_financial is not available
            row_irr = calculate_simple_irr_fallback(sm_value, gross_profit_columns)
        
        row_data['IRR'] = row_irr
        table_data.append(row_data)
    
    # Note: No summary row added - keeping only the original data rows
    
    df = pd.DataFrame(table_data)
    print(f"✅ {label} gross profit table created: {df.shape[0]:,} rows x {df.shape[1]} columns")
    return df
    
    # Add summary row
    print(f"  Adding summary row...")
    summary_row = {}
    df_temp = pd.DataFrame(table_data)
    
    # Calculate column sums (excluding B and BL which will be calculated)
    for col in df_temp.columns:
        if col not in ['Predicted_Ratio', 'LTV_to_CAC']:  # B and BL columns
            summary_row[col] = df_temp[col].sum()
    
    # Calculate B (Predicted_Ratio) = A (SM_Value) / C (SM_Divided_By_Ratio)
    if summary_row['SM_Value'] != 0 and summary_row['SM_Divided_By_Ratio'] != 0:
        summary_row['Predicted_Ratio'] = summary_row['SM_Value'] / summary_row['SM_Divided_By_Ratio']
    else:
        summary_row['Predicted_Ratio'] = None
    
    # Calculate BL (LTV_to_CAC) = sum(D to BK) / A
    revenue_sum = sum([summary_row[f'Revenue_Month_{i}'] for i in range(1, 61) if summary_row[f'Revenue_Month_{i}'] is not None])
    if summary_row['SM_Value'] != 0:
        summary_row['LTV_to_CAC'] = revenue_sum / summary_row['SM_Value']
    else:
        summary_row['LTV_to_CAC'] = None
    
    # Add summary row to table data
    table_data.append(summary_row)
    
    # Add NDR row
    print(f"  Adding NDR row...")
    ndr_row = {}
    for col in df_temp.columns:
        if col == 'SM_Value':
            ndr_row[col] = 'NDR'
        elif col == 'Predicted_Ratio':
            ndr_row[col] = None
        elif col == 'SM_Divided_By_Ratio':
            ndr_row[col] = None
        elif col == 'Revenue_Month_1':
            ndr_row[col] = None
        elif col.startswith('Revenue_Month_'):
            month_num = int(col.split('_')[2])
            if month_num >= 2:  # Columns E to BK (Revenue_Month_2 to Revenue_Month_60)
                if summary_row['Revenue_Month_1'] is not None and summary_row['Revenue_Month_1'] != 0:
                    ndr_row[col] = summary_row[col] / summary_row['Revenue_Month_1'] if summary_row[col] is not None else None
                else:
                    ndr_row[col] = None
            else:
                ndr_row[col] = None
        elif col.startswith('Gross_Profit_Month_'):
            # For gross profit columns, set to None in NDR row (not applicable)
            ndr_row[col] = None
        elif col == 'LTV_to_CAC':
            ndr_row[col] = None
        else:
            ndr_row[col] = None
    
    # Add NDR row to table data
    table_data.append(ndr_row)
    
    df = pd.DataFrame(table_data)
    print(f"✅ {label} table created: {df.shape[0]:,} rows x {df.shape[1]} columns (including summary and NDR rows)")
    return df

def create_comprehensive_table():
    print("🚀 CREATING CONSERVATIVE AND LESS CONSERVATIVE GROSS PROFIT SIMULATION TABLES")
    print("=" * 60)
    print("Each table: S&M | 60 Gross Profit Columns | LTV/CAC | IRR")
    print("Rows: 1,000 (from Monte Carlo simulations)")  # Updated from 12,000
    print("Columns: 63 total (1 S&M + 60 gross profit + 1 LTV/CAC + 1 IRR)")
    print("Gross_Profit_Month_1 = (S&M/Ratio) × Gross_Margin")
    print("Gross_Profit_Month_n = (Revenue_Month_n × Gross_Margin) where Revenue_Month_n = Revenue_Month_{n-1} × Retention_Month_n")
    print("Gross_Margin = minimum of (overall, last 12 months, median monthly)")
    print("LTV/CAC = sum(all gross profit columns) / S&M expense")
    print("IRR = Internal Rate of Return for cash flow: [-S&M_Value, Gross_Profit_Month_1, Gross_Profit_Month_2, ...]")
    
    # Step 1: Run Monte Carlo simulation for 1,000 paired values
    print(f"\n📊 Step 1: Running Monte Carlo simulation...")
    simulation_results = run_monte_carlo_predicted_ratio(num_simulations=1000)  # Changed from 1000 * 12 = 12,000 to just 1000
    conservative_simulations = simulation_results['conservative']['simulations']
    less_conservative_simulations = simulation_results['less_conservative']['simulations']
    print(f"✅ Generated {len(conservative_simulations):,} conservative and {len(less_conservative_simulations):,} less conservative paired values")
    
    # Step 2: Run retention curve simulation 1 time to get 1,000 curves for each scenario
    print(f"\n📊 Step 2: Running retention curve simulation...")
    print("Running retention simulation 1 time to get 1,000 curves for each scenario...")  # Updated message
    
    # Generate conservative retention curves
    print("  Generating conservative retention curves...")
    conservative_retention_curves = []
    for run in range(1):  # Changed from 12 to 1
        print(f"    Conservative retention run {run + 1}/1...")  # Updated message
        retention_curves, _ = simulate_1000_retention_curves(conservative=True)
        conservative_retention_curves.extend(retention_curves)  # Take all 1000 from each run
    
    # Generate less conservative retention curves
    print("  Generating less conservative retention curves...")
    less_conservative_retention_curves = []
    for run in range(1):  # Changed from 12 to 1
        print(f"    Less conservative retention run {run + 1}/1...")  # Updated message
        retention_curves, _ = simulate_1000_retention_curves(conservative=False)
        less_conservative_retention_curves.extend(retention_curves)  # Take all 1000 from each run
    
    print(f"✅ Generated {len(conservative_retention_curves):,} conservative retention curves")
    print(f"✅ Generated {len(less_conservative_retention_curves):,} less conservative retention curves")
    
    # Step 3: Build gross profit tables
    df_conservative = build_gross_profit_table(conservative_simulations, conservative_retention_curves, "Conservative")
    df_less_conservative = build_gross_profit_table(less_conservative_simulations, less_conservative_retention_curves, "Less Conservative")
    
    # Step 4: Export to Excel (one file per table)
    for label, df in [("conservative", df_conservative), ("less_conservative", df_less_conservative)]:
        print(f"\n📊 Step 4: Exporting {label} table to Excel...")
        filename = f"gross_profit_simulation_{label}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            print("  Writing main gross profit table...")
            df.to_excel(writer, sheet_name='Gross_Profit_Simulation', index=False)
            print("  Creating summary statistics...")
            summary_data = {
                'Metric': [
                    'Total Rows',
                    'Total Columns',
                    'S&M Values',
                    'Gross Profit Months',
                    'LTV/CAC Values',
                    'Data Points',
                    'Monte Carlo Simulations',
                    'Retention Curve Runs',
                    'Summary Row'
                ],
                'Value': [
                    len(df),
                    len(df.columns),
                    len(df['SM_Value'].dropna()),
                    60,
                    len(df['LTV_to_CAC'].dropna()),
                    len(df) * len(df.columns),
                    1000,
                    1,
                    'Yes (sum of all data rows)'
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            print("  Creating sample data sheet...")
            sample_df = df.head(10)
            sample_df.to_excel(writer, sheet_name='Sample_Data', index=False)
            print("  Creating column descriptions...")
            column_descriptions = {
                'Column': [
                    'SM_Value',
                    'Gross_Profit_Month_1 through Gross_Profit_Month_60',
                    'LTV_to_CAC',
                    'IRR'
                ],
                'Description': [
                    'S&M spending value from Monte Carlo simulation',
                    'Gross profit projections for months 1-60 (Revenue × Gross Margin)',
                    'Sum of all gross profit columns divided by S&M value (LTV/CAC)',
                    'Internal Rate of Return for cash flow: [-S&M_Value, Gross_Profit_Month_1, Gross_Profit_Month_2, ...]'
                ],
                'Data Type': [
                    'Float',
                    'Float (gross profit values)',
                    'Float',
                    'Float (IRR as decimal)'
                ]
            }
            desc_df = pd.DataFrame(column_descriptions)
            desc_df.to_excel(writer, sheet_name='Column_Descriptions', index=False)
            print("  Creating metadata sheet...")
            metadata = {
                'Parameter': [
                    'Table Type',
                    'Monte Carlo Simulations',
                    'Retention Curve Runs',
                    'Gross Profit Calculation',
                    'LTV/CAC Calculation',
                    'IRR Calculation',
                    'Total Rows',
                    'Total Columns',
                    'Data Points',
                    'Summary Row',
                    'Generated Date'
                ],
                'Value': [
                    f'Gross Profit Simulation Table ({label})',
                    '1,000 (1,000 paired values)',  # Updated from 12,000
                    '1 run (1,000 curves)',  # Updated from 12 runs
                    'Gross_Profit_Month_1 = (S&M/Ratio) × Gross_Margin; Gross_Profit_Month_n = (Revenue_Month_n × Gross_Margin)',
                    'Sum of all gross profit columns divided by S&M value',
                    'IRR for cash flow: [-S&M_Value, Gross_Profit_Month_1, Gross_Profit_Month_2, ...]',
                    f"{len(df):,}",
                    f"{len(df.columns)}",
                    f"{len(df) * len(df.columns):,}",
                    'Sum of all columns except LTV_to_CAC and IRR; LTV_to_CAC = sum(all gross profit columns) / SM_Value; IRR = average of all row IRRs',
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ]
            }
            metadata_df = pd.DataFrame(metadata)
            metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
        print(f"✅ Gross profit simulation Excel file created: {filename}")
        print(f"📋 Sheets included:")
        print(f"  - Gross_Profit_Simulation: Main data table ({len(df):,} rows x {len(df.columns)} columns)")  # Updated to use dynamic values
        print(f"  - Summary: Dataset statistics")
        print(f"  - Sample_Data: First 10 rows for quick review")
        print(f"  - Column_Descriptions: Explanation of each column")
        print(f"  - Metadata: File information and parameters")
        print(f"📊 Total data points: {len(df) * len(df.columns):,}")
        print(f"💰 Gross profit calculation: Revenue × Gross Margin (minimum of overall, last 12 months, median monthly)")
        print(f"💡 LTV/CAC = sum(all gross profit columns) / S&M expense")
        print(f"📈 IRR = Internal Rate of Return for each row's cash flow")

if __name__ == "__main__":
    create_comprehensive_table() 