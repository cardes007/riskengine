#!/usr/bin/env python3
"""
Fund Performance Model
Analyzes 12,000 cohort simulations to model fund returns based on lending terms:
- Lend 80% of S&M expense
- Receive 80% of gross profit until 16% return or year 5
"""

import pandas as pd
import json
from datetime import datetime
from create_comprehensive_table import build_gross_profit_table, calculate_gross_margin
from monte_carlo_predicted_ratio import run_monte_carlo_predicted_ratio
from simulate_1000_retention_curves import simulate_1000_retention_curves

def calculate_fund_returns_for_cohort(sm_value, gross_profit_series, target_irr=0.16, max_years=5):
    """
    Calculate fund returns for a single cohort using IRR
    
    Args:
        sm_value: S&M expense (positive value)
        gross_profit_series: List of 60 monthly gross profit values
        target_irr: Target IRR (16% = 0.16)
        max_years: Maximum years to track (5 years = 60 months)
    
    Returns:
        dict with fund performance metrics
    """
    # Fund lends 80% of S&M
    loan_amount = sm_value * 0.8
    
    # Calculate monthly returns (80% of gross profit)
    monthly_returns = []
    cumulative_return = 0
    months_to_target = None
    months_to_max_years = None
    return_reached = False
    
    for month in range(min(60, max_years * 12)):
        if gross_profit_series[month] is not None and gross_profit_series[month] > 0:
            monthly_gross_profit = gross_profit_series[month]
            fund_return = monthly_gross_profit * 0.8
            monthly_returns.append(fund_return)
            cumulative_return += fund_return
        else:
            monthly_returns.append(0)
    
    # If we reached max years, record that
    if len(monthly_returns) >= max_years * 12:
        months_to_max_years = max_years * 12
    
    # Calculate IRR for the cash flow
    # Cash flow: [-loan_amount, monthly_returns[0], monthly_returns[1], ...]
    cash_flow = [-loan_amount] + monthly_returns
    
    # Calculate IRR using numpy's financial functions
    try:
        import numpy as np
        from numpy_financial import irr
        
        # Filter out None values and ensure we have valid cash flows
        valid_cash_flow = [cf for cf in cash_flow if cf is not None]
        if len(valid_cash_flow) > 1 and valid_cash_flow[0] < 0:
            calculated_irr = irr(valid_cash_flow)
            if calculated_irr is not None and np.isfinite(calculated_irr):
                actual_irr = calculated_irr
            else:
                actual_irr = 0
        else:
            actual_irr = 0
    except ImportError:
        # Fallback IRR calculation if numpy_financial is not available
        actual_irr = calculate_simple_irr(loan_amount, monthly_returns)
    
    # Check if target IRR is reached and find the stopping point
    months_to_target = None
    return_reached = False
    final_monthly_returns = monthly_returns.copy()
    
    # Find the month when IRR target is reached
    for month in range(len(monthly_returns)):
        partial_cash_flow = [-loan_amount] + monthly_returns[:month+1]
        try:
            partial_irr = irr(partial_cash_flow)
            if partial_irr is not None and partial_irr >= target_irr:
                months_to_target = month + 1
                return_reached = True
                # Stop receiving payments after this month (set remaining months to 0)
                for i in range(month + 1, len(final_monthly_returns)):
                    final_monthly_returns[i] = 0
                break
        except:
            continue
    
    # Recalculate cumulative return with the capped payments
    final_cumulative_return = sum(final_monthly_returns)
    
    # Calculate the final IRR with capped payments
    final_cash_flow = [-loan_amount] + final_monthly_returns
    try:
        final_irr = irr(final_cash_flow)
        if final_irr is not None and np.isfinite(final_irr):
            actual_irr = final_irr
        else:
            actual_irr = 0
    except:
        actual_irr = calculate_simple_irr(loan_amount, final_monthly_returns)
    
    # Calculate the target return amount based on IRR
    target_return_amount = calculate_target_return_for_irr(loan_amount, target_irr, months_to_target if months_to_target else max_years * 12)
    
    # Final return is the cumulative return with capped payments
    final_return = final_cumulative_return
    
    # Calculate actual return percentage (simple return, not IRR)
    actual_return_pct = (final_return / loan_amount) if loan_amount > 0 else 0
    
    return {
        'loan_amount': loan_amount,
        'target_irr': target_irr,
        'actual_irr': actual_irr,
        'target_return_amount': target_return_amount,
        'final_return': final_return,
        'actual_return_pct': actual_return_pct,
        'months_to_target': months_to_target,
        'months_to_max_years': months_to_max_years,
        'return_reached': return_reached,
        'cumulative_return': cumulative_return,
        'final_cumulative_return': final_cumulative_return,
        'monthly_returns': monthly_returns[:60],  # Original monthly returns
        'final_monthly_returns': final_monthly_returns[:60]  # Capped monthly returns
    }

def calculate_simple_irr(loan_amount, monthly_returns):
    """
    Simple IRR calculation fallback
    """
    if loan_amount <= 0:
        return 0
    
    total_return = sum(monthly_returns)
    if total_return <= 0:
        return -1  # Negative IRR
    
    # Simple approximation: assume average time to receive returns
    avg_month = sum(i * ret for i, ret in enumerate(monthly_returns) if ret > 0) / total_return if total_return > 0 else 0
    avg_years = avg_month / 12
    
    # Simple IRR approximation
    if avg_years > 0:
        return (total_return / loan_amount) ** (1 / avg_years) - 1
    else:
        return 0

def calculate_target_return_for_irr(loan_amount, target_irr, months):
    """
    Calculate the target return amount needed to achieve the target IRR
    """
    if months <= 0:
        return loan_amount * target_irr
    
    # For monthly IRR, convert annual IRR to monthly
    monthly_irr = (1 + target_irr) ** (1/12) - 1
    
    # Calculate the future value needed
    target_fv = loan_amount * (1 + monthly_irr) ** months
    
    # The target return is the difference
    target_return = target_fv - loan_amount
    
    return target_return

def analyze_fund_performance():
    """
    Analyze fund performance across all 12,000 simulations
    """
    print("🚀 FUND PERFORMANCE ANALYSIS")
    print("=" * 60)
    print("Lending Terms:")
    print("  - Lend 80% of S&M expense")
    print("  - Receive 80% of gross profit")
    print("  - Stop receiving payments when 16% IRR is reached")
    print("  - Maximum return per loan is capped at 16% IRR")
    print("  - IRR accounts for time value of money")
    print("=" * 60)
    
    # Step 1: Run Monte Carlo simulation for 1,000 paired values
    print(f"\n📊 Step 1: Running Monte Carlo simulation...")
    simulation_results = run_monte_carlo_predicted_ratio(num_simulations=1000)  # 1000 * 12 = 12,000 paired values
    conservative_simulations = simulation_results['conservative']['simulations']
    less_conservative_simulations = simulation_results['less_conservative']['simulations']
    print(f"✅ Generated {len(conservative_simulations):,} conservative and {len(less_conservative_simulations):,} less conservative paired values")
    
    # Step 2: Run retention curve simulation 1 time to get 1,000 curves for each scenario
    print(f"\n📊 Step 2: Running retention curve simulation...")
    print("Running retention simulation 1 time to get 1,000 curves for each scenario...")
    
    # Generate conservative retention curves
    print("  Generating conservative retention curves...")
    conservative_retention_curves = []
    for run in range(1):  # Changed from 12 to 1
        print(f"    Conservative retention run {run + 1}/1...")  # Updated message
        retention_curves, _ = simulate_1000_retention_curves(conservative=True)
        conservative_retention_curves.extend(retention_curves)
    
    # Generate less conservative retention curves
    print("  Generating less conservative retention curves...")
    less_conservative_retention_curves = []
    for run in range(1):  # Changed from 12 to 1
        print(f"    Less conservative retention run {run + 1}/1...")  # Updated message
        retention_curves, _ = simulate_1000_retention_curves(conservative=False)
        less_conservative_retention_curves.extend(retention_curves)
    
    print(f"✅ Generated {len(conservative_retention_curves):,} conservative retention curves")
    print(f"✅ Generated {len(less_conservative_retention_curves):,} less conservative retention curves")
    
    # Step 3: Build gross profit tables
    print(f"\n📊 Step 3: Building gross profit tables...")
    df_conservative = build_gross_profit_table(conservative_simulations, conservative_retention_curves, "Conservative")
    df_less_conservative = build_gross_profit_table(less_conservative_simulations, less_conservative_retention_curves, "Less Conservative")
    
    # Step 4: Analyze fund performance for both scenarios
    scenarios = [
        ("conservative", df_conservative),
        ("less_conservative", df_less_conservative)
    ]
    
    for scenario_name, df in scenarios:
        print(f"\n📊 Step 4: Analyzing {scenario_name} scenario...")
        
        # Remove summary row if present
        if df.iloc[-1]['SM_Value'] == 'NDR' or df.iloc[-1]['SM_Value'] < 0:
            df = df.iloc[:-1]  # Remove summary row
        
        fund_results = []
        total_loan_amount = 0
        total_final_return = 0
        
        for idx, row in df.iterrows():
            if idx % 100 == 0:  # Changed from 1000 to 100 for more frequent updates
                print(f"  Processing cohort {idx + 1:,}/1,000...")  # Updated from 12,000 to 1,000
            
            # Get S&M value (convert back to positive for calculations)
            sm_value = abs(row['SM_Value'])
            
            # Get gross profit series (60 months)
            gross_profit_series = []
            for month in range(1, 61):
                col_name = f'Gross_Profit_Month_{month}'
                if col_name in row:
                    gross_profit_series.append(row[col_name])
                else:
                    gross_profit_series.append(None)
            
            # Calculate fund returns for this cohort
            cohort_result = calculate_fund_returns_for_cohort(sm_value, gross_profit_series)
            
            # Add cohort info
            cohort_result['cohort_id'] = idx
            cohort_result['sm_value'] = sm_value
            fund_results.append(cohort_result)
            
            total_loan_amount += cohort_result['loan_amount']
            total_final_return += cohort_result['final_return']
        
        # Calculate fund-level metrics
        total_cohorts = len(fund_results)
        avg_loan_amount = total_loan_amount / total_cohorts
        avg_final_return = total_final_return / total_cohorts
        overall_return_pct = (total_final_return / total_loan_amount) if total_loan_amount > 0 else 0
        
        # Calculate distribution statistics for both simple returns and IRR
        return_pcts = [r['actual_return_pct'] for r in fund_results]
        irr_values = [r['actual_irr'] for r in fund_results]
        
        return_pcts_sorted = sorted(return_pcts)
        irr_values_sorted = sorted(irr_values)
        
        # Percentiles for simple returns
        p25 = return_pcts_sorted[int(0.25 * len(return_pcts_sorted))]
        p50 = return_pcts_sorted[int(0.50 * len(return_pcts_sorted))]
        p75 = return_pcts_sorted[int(0.75 * len(return_pcts_sorted))]
        p90 = return_pcts_sorted[int(0.90 * len(return_pcts_sorted))]
        p95 = return_pcts_sorted[int(0.95 * len(return_pcts_sorted))]
        
        # Percentiles for IRR
        irr_p25 = irr_values_sorted[int(0.25 * len(irr_values_sorted))]
        irr_p50 = irr_values_sorted[int(0.50 * len(irr_values_sorted))]
        irr_p75 = irr_values_sorted[int(0.75 * len(irr_values_sorted))]
        irr_p90 = irr_values_sorted[int(0.90 * len(irr_values_sorted))]
        irr_p95 = irr_values_sorted[int(0.95 * len(irr_values_sorted))]
        
        # Calculate average IRR
        avg_irr = sum(irr_values) / len(irr_values) if irr_values else 0
        
        # Count cohorts that reached target IRR
        cohorts_reached_target = sum(1 for r in fund_results if r['return_reached'])
        pct_reached_target = (cohorts_reached_target / total_cohorts) * 100
        
        # Count cohorts that hit max years
        cohorts_hit_max_years = sum(1 for r in fund_results if r['months_to_max_years'] is not None)
        pct_hit_max_years = (cohorts_hit_max_years / total_cohorts) * 100
        
        # Print results
        print(f"\n📈 {scenario_name.upper()} SCENARIO RESULTS")
        print("=" * 50)
        print(f"Total Cohorts: {total_cohorts:,}")
        print(f"Total Loan Amount: ${total_loan_amount:,.0f}")
        print(f"Total Final Return: ${total_final_return:,.0f}")
        print(f"Overall Simple Return: {overall_return_pct:.2%}")
        print(f"Average IRR: {avg_irr:.2%}")
        print(f"Average Loan per Cohort: ${avg_loan_amount:,.0f}")
        print(f"Average Return per Cohort: ${avg_final_return:,.0f}")
        print(f"\n📊 Simple Return Distribution:")
        print(f"  25th Percentile: {p25:.2%}")
        print(f"  50th Percentile (Median): {p50:.2%}")
        print(f"  75th Percentile: {p75:.2%}")
        print(f"  90th Percentile: {p90:.2%}")
        print(f"  95th Percentile: {p95:.2%}")
        print(f"\n📊 IRR Distribution:")
        print(f"  25th Percentile: {irr_p25:.2%}")
        print(f"  50th Percentile (Median): {irr_p50:.2%}")
        print(f"  75th Percentile: {irr_p75:.2%}")
        print(f"  90th Percentile: {irr_p90:.2%}")
        print(f"  95th Percentile: {irr_p95:.2%}")
        print(f"\n🎯 Target IRR Analysis:")
        print(f"  Cohorts reaching 16% IRR: {cohorts_reached_target:,} ({pct_reached_target:.1f}%)")
        print(f"  Cohorts hitting 5-year limit: {cohorts_hit_max_years:,} ({pct_hit_max_years:.1f}%)")
        
        # Export detailed results
        filename = f"fund_performance_{scenario_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        print(f"\n📊 Exporting detailed results to {filename}...")
        
        # Create DataFrame for export
        export_data = []
        for result in fund_results:
            export_data.append({
                'Cohort_ID': result['cohort_id'],
                'S&M_Value': result['sm_value'],
                'Loan_Amount': result['loan_amount'],
                'Target_IRR': result['target_irr'],
                'Actual_IRR': result['actual_irr'],
                'Target_Return_Amount': result['target_return_amount'],
                'Final_Return': result['final_return'],
                'Actual_Return_Pct': result['actual_return_pct'],
                'Months_to_Target': result['months_to_target'],
                'Months_to_Max_Years': result['months_to_max_years'],
                'Return_Reached': result['return_reached'],
                'Original_Cumulative_Return': result['cumulative_return'],
                'Capped_Cumulative_Return': result['final_cumulative_return']
            })
        
        df_export = pd.DataFrame(export_data)
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Main results
            df_export.to_excel(writer, sheet_name='Fund_Results', index=False)
            
            # Summary statistics
            summary_data = {
                'Metric': [
                    'Total Cohorts',
                    'Total Loan Amount',
                    'Total Final Return',
                    'Overall Simple Return %',
                    'Average IRR %',
                    'Average Loan per Cohort',
                    'Average Return per Cohort',
                    'Cohorts Reaching 16% IRR',
                    'Cohorts Hitting 5-Year Limit',
                    '25th Percentile Simple Return',
                    '50th Percentile Simple Return',
                    '75th Percentile Simple Return',
                    '90th Percentile Simple Return',
                    '95th Percentile Simple Return',
                    '25th Percentile IRR',
                    '50th Percentile IRR',
                    '75th Percentile IRR',
                    '90th Percentile IRR',
                    '95th Percentile IRR'
                ],
                'Value': [
                    total_cohorts,
                    f"${total_loan_amount:,.0f}",
                    f"${total_final_return:,.0f}",
                    f"{overall_return_pct:.2%}",
                    f"{avg_irr:.2%}",
                    f"${avg_loan_amount:,.0f}",
                    f"${avg_final_return:,.0f}",
                    f"{cohorts_reached_target:,} ({pct_reached_target:.1f}%)",
                    f"{cohorts_hit_max_years:,} ({pct_hit_max_years:.1f}%)",
                    f"{p25:.2%}",
                    f"{p50:.2%}",
                    f"{p75:.2%}",
                    f"{p90:.2%}",
                    f"{p95:.2%}",
                    f"{irr_p25:.2%}",
                    f"{irr_p50:.2%}",
                    f"{irr_p75:.2%}",
                    f"{irr_p90:.2%}",
                    f"{irr_p95:.2%}"
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Monthly returns for first 10 cohorts (showing capped returns)
            monthly_data = []
            for i in range(min(10, len(fund_results))):
                result = fund_results[i]
                row_data = {'Cohort_ID': result['cohort_id']}
                for month in range(60):
                    if month < len(result['final_monthly_returns']):
                        row_data[f'Month_{month+1}'] = result['final_monthly_returns'][month]
                    else:
                        row_data[f'Month_{month+1}'] = 0
                monthly_data.append(row_data)
            
            monthly_df = pd.DataFrame(monthly_data)
            monthly_df.to_excel(writer, sheet_name='Sample_Monthly_Returns', index=False)
        
        print(f"✅ Fund performance analysis exported to {filename}")
        print(f"📋 Sheets included:")
        print(f"  - Fund_Results: Detailed results for all 12,000 cohorts")
        print(f"  - Summary: Key performance metrics")
        print(f"  - Sample_Monthly_Returns: Monthly returns for first 10 cohorts")

if __name__ == "__main__":
    analyze_fund_performance() 