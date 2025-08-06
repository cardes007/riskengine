import pandas as pd
import json
from datetime import datetime
from monte_carlo_predicted_ratio import run_monte_carlo_predicted_ratio

def combine_predicted_ratios_and_retention_curves():
    print("🚀 COMBINING PREDICTED RATIOS, S&M VALUES, AND RETENTION CURVES")
    print("=" * 70)
    
    # Step 1: Run Monte Carlo simulation to get predicted ratios and S&M values
    print("📊 Step 1: Running Monte Carlo simulation for predicted ratios and S&M values...")
    simulation_results = run_monte_carlo_predicted_ratio(num_simulations=120000)
    
    # Extract predicted ratios and S&M values
    conservative_ratios = simulation_results['conservative']['predicted_ratios']
    conservative_sm_values = simulation_results['conservative']['sm_values']
    less_conservative_ratios = simulation_results['less_conservative']['predicted_ratios']
    less_conservative_sm_values = simulation_results['less_conservative']['sm_values']
    
    print(f"✅ Generated {len(conservative_ratios):,} conservative predicted ratios")
    print(f"✅ Generated {len(conservative_sm_values):,} conservative S&M values")
    print(f"✅ Generated {len(less_conservative_ratios):,} less conservative predicted ratios")
    print(f"✅ Generated {len(less_conservative_sm_values):,} less conservative S&M values")
    
    # Step 2: Load retention curves data
    print(f"\n📊 Step 2: Loading retention curves data...")
    retention_file = "retention_curves_120000_simulations_20250723_002952.xlsx"
    
    try:
        retention_df = pd.read_excel(retention_file, sheet_name='Simulations', index_col=0)
        print(f"✅ Loaded retention curves: {retention_df.shape[0]:,} simulations x {retention_df.shape[1]} months")
    except FileNotFoundError:
        print(f"❌ Error: Could not find {retention_file}")
        print("Please ensure the retention curves Excel file exists in the current directory.")
        return None
    
    # Step 3: Create combined dataset
    print(f"\n📊 Step 3: Creating combined dataset...")
    
    # Create DataFrame with predicted ratios and S&M values as first columns
    combined_data = {}
    
    # Add conservative predicted ratios and S&M values
    combined_data['Conservative_Predicted_Ratio'] = conservative_ratios[:len(retention_df)]
    combined_data['Conservative_SM_Value'] = conservative_sm_values[:len(retention_df)]
    
    # Add less conservative predicted ratios and S&M values
    combined_data['Less_Conservative_Predicted_Ratio'] = less_conservative_ratios[:len(retention_df)]
    combined_data['Less_Conservative_SM_Value'] = less_conservative_sm_values[:len(retention_df)]
    
    # Add all retention curve columns
    for col in retention_df.columns:
        combined_data[col] = retention_df[col].values
    
    # Create combined DataFrame
    combined_df = pd.DataFrame(combined_data)
    
    # Set index to match retention curves
    combined_df.index = retention_df.index
    
    print(f"✅ Combined dataset created: {combined_df.shape[0]:,} rows x {combined_df.shape[1]} columns")
    print(f"   - 4 prediction columns (2 ratios + 2 S&M values)")
    print(f"   - {len(retention_df.columns)} retention curve columns")
    
    # Step 4: Export to Excel
    print(f"\n📊 Step 4: Exporting to Excel...")
    filename = f"combined_predictions_and_retention_curves_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # Main combined data sheet
        print("  Writing main combined data sheet...")
        combined_df.to_excel(writer, sheet_name='Combined_Data', index=True)
        
        # Summary statistics for predicted ratios and S&M values
        print("  Creating summary statistics...")
        summary_data = {
            'Metric': [
                'Conservative Predicted Ratios',
                'Conservative S&M Values',
                'Less Conservative Predicted Ratios',
                'Less Conservative S&M Values',
                'Total Simulations',
                'Retention Curve Months',
                'Combined Data Points'
            ],
            'Value': [
                len(conservative_ratios),
                len(conservative_sm_values),
                len(less_conservative_ratios),
                len(less_conservative_sm_values),
                len(combined_df),
                len(retention_df.columns),
                len(combined_df) * len(combined_df.columns)
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Sample data sheet (first 10 rows)
        print("  Creating sample data sheet...")
        sample_df = combined_df.head(10)
        sample_df.to_excel(writer, sheet_name='Sample_Data', index=True)
        
        # Metadata sheet
        print("  Creating metadata sheet...")
        metadata = {
            'Parameter': [
                'Combined Dataset Type',
                'Conservative Predicted Ratios',
                'Conservative S&M Values',
                'Less Conservative Predicted Ratios',
                'Less Conservative S&M Values',
                'Retention Curves Source',
                'Total Rows',
                'Total Columns',
                'Data Points',
                'Generated Date'
            ],
            'Value': [
                'Predictions + Retention Curves',
                f"{len(conservative_ratios):,} values",
                f"{len(conservative_sm_values):,} values",
                f"{len(less_conservative_ratios):,} values",
                f"{len(less_conservative_sm_values):,} values",
                retention_file,
                f"{len(combined_df):,}",
                f"{len(combined_df.columns)}",
                f"{len(combined_df) * len(combined_df.columns):,}",
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ]
        }
        metadata_df = pd.DataFrame(metadata)
        metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
    
    print(f"✅ Combined Excel file created: {filename}")
    print(f"📋 Sheets included:")
    print(f"  - Combined_Data: All data (predictions + retention curves)")
    print(f"  - Summary: Dataset statistics")
    print(f"  - Sample_Data: First 10 rows for quick review")
    print(f"  - Metadata: File information and parameters")
    print(f"📊 Total data points: {len(combined_df) * len(combined_df.columns):,}")
    
    return filename

if __name__ == "__main__":
    combine_predicted_ratios_and_retention_curves() 