import pandas as pd
from datetime import datetime
from simulate_1000_retention_curves import simulate_120000_retention_curves

def export_simulations_to_excel():
    print("🚀 Starting 120,000 retention curve simulations...")
    
    # Run the simulations
    all_curves, transition_month = simulate_120000_retention_curves()
    
    print(f"\n📊 Creating Excel file...")
    
    # Create DataFrame
    # Each row is a simulation, each column is a month
    df = pd.DataFrame(all_curves)
    
    # Rename columns to Month 1, Month 2, etc.
    df.columns = [f'Month_{i+1}' for i in range(60)]
    
    # Add simulation number as index
    df.index = [f'Simulation_{i+1}' for i in range(120000)]
    
    # Create Excel file with multiple sheets
    filename = f"retention_curves_120000_simulations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # Main data sheet - write in chunks to handle large dataset
        print("  Writing main simulations sheet...")
        chunk_size = 10000
        for i in range(0, len(df), chunk_size):
            chunk = df.iloc[i:i+chunk_size]
            if i == 0:
                chunk.to_excel(writer, sheet_name='Simulations', index=True)
            else:
                chunk.to_excel(writer, sheet_name='Simulations', index=True, 
                             startrow=i+1, header=False)
        
        # Summary statistics sheet
        print("  Creating summary statistics...")
        summary_data = []
        for col in df.columns:
            month_num = int(col.split('_')[1])
            non_null_values = df[col].dropna()
            if len(non_null_values) > 0:
                summary_data.append({
                    'Month': month_num,
                    'Mean': non_null_values.mean(),
                    'Median': non_null_values.median(),
                    'Std': non_null_values.std(),
                    'Min': non_null_values.min(),
                    'Max': non_null_values.max(),
                    'Count': len(non_null_values)
                })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary_Statistics', index=False)
        
        # Sample curves sheet (first 10 simulations)
        print("  Creating sample curves sheet...")
        sample_df = df.head(10)
        sample_df.to_excel(writer, sheet_name='Sample_Curves', index=True)
        
        # Metadata sheet
        print("  Creating metadata sheet...")
        metadata = {
            'Parameter': [
                'Total Simulations',
                'Months per Simulation',
                'Transition Month (Column-specific to Global)',
                'Minimum NDR 12th Root',
                'Excluded Rows',
                'Generated Date'
            ],
            'Value': [
                120000,
                60,
                transition_month if transition_month else 'All months have sufficient data',
                'See simulate_retention_curve.py for calculation',
                'Older Cohorts row (excluded from column-specific sampling)',
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ]
        }
        metadata_df = pd.DataFrame(metadata)
        metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
    
    print(f"✅ Excel file created: {filename}")
    print(f"📋 Sheets included:")
    print(f"  - Simulations: All 120,000 simulations (60 months each)")
    print(f"  - Summary_Statistics: Statistical summary by month")
    print(f"  - Sample_Curves: First 10 simulations for quick review")
    print(f"  - Metadata: Simulation parameters and settings")
    print(f"📊 Total data points: {120000 * 60:,}")
    
    return filename

if __name__ == "__main__":
    export_simulations_to_excel() 