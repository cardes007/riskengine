import pandas as pd
import numpy as np
from datetime import datetime
import os
import sys
from lender_cashflow_calculator import calculate_lender_cashflows

# Add the current directory to the path so we can import create_comprehensive_table
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from create_comprehensive_table import create_comprehensive_table

def transform_gross_profit_to_lender_cashflows(input_file, output_file, loan_percentage=0.80, yearly_interest_rate=0.16):
    """
    Transform gross profit simulation data to lender cash flows.
    
    Args:
        input_file (str): Path to the gross profit simulation Excel file
        output_file (str): Path for the output lender cash flow Excel file
        loan_percentage (float): Percentage of S&M to lend (default 80%)
        yearly_interest_rate (float): Yearly interest rate as decimal (default 16%)
    
    Returns:
        dict: Summary statistics including total loan amount, total net return, and positive return rate
    """
    print(f"🔄 Transforming {input_file} to lender cash flows...")
    print(f"📊 Parameters: {loan_percentage*100:.0f}% loan, {yearly_interest_rate*100:.0f}% yearly interest")
    
    # Read the gross profit simulation data
    try:
        # Try to read from Gross_Profit_Simulation sheet first (original files)
        try:
            df = pd.read_excel(input_file, sheet_name='Gross_Profit_Simulation')
            print(f"✅ Loaded {len(df)} rows from Gross_Profit_Simulation sheet")
        except:
            # If that fails, try Aggregated_Simulation sheet (aggregated files)
            df = pd.read_excel(input_file, sheet_name='Aggregated_Simulation')
            print(f"✅ Loaded {len(df)} rows from Aggregated_Simulation sheet")
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return
    
    # Initialize lender cash flow data
    lender_data = []
    
    # Process each row
    for idx, row in df.iterrows():
        if idx % 1000 == 0:
            print(f"  Processing row {idx:,}/{len(df):,}...")
        
        # Skip summary and NDR rows
        if pd.isna(row['SM_Value']) or row['SM_Value'] == 'NDR':
            continue
        
        sm_value = abs(row['SM_Value'])  # Convert back to positive
        
        # Extract gross profit cash flows
        gross_profit_cashflows = [-sm_value]  # Initial investment (negative)
        
        # Add monthly gross profits
        for month in range(1, 61):
            col_name = f'Gross_Profit_Month_{month}'
            if col_name in row and pd.notna(row[col_name]):
                gross_profit_cashflows.append(row[col_name])
            else:
                gross_profit_cashflows.append(0)
        
        # Calculate lender cash flows
        try:
            lender_cashflows, loan_info = calculate_lender_cashflows(
                gross_profit_cashflows,
                loan_percentage=loan_percentage,
                yearly_interest_rate=yearly_interest_rate
            )
        except Exception as e:
            print(f"Error calculating lender cash flows for row {idx}: {e}")
            lender_cashflows = [0] * 61
            loan_info = {'net_return': 0, 'loan_amount': 0, 'total_payments_received': 0}
        
        # Create lender row data
        lender_row = {
            'Loan_Amount': -loan_info['loan_amount'],  # Loan amount as negative (first column)
        }
        
        # Add lender cash flows (skip first one as it's the loan amount)
        for month in range(1, 61):
            lender_row[f'Lender_Cashflow_Month_{month}'] = lender_cashflows[month] if month < len(lender_cashflows) else 0
        
        # Store loan metrics for summary calculations (not in main table)
        lender_row['_Net_Return'] = loan_info['net_return']
        lender_row['_Total_Payments'] = loan_info['total_payments_received']
        lender_row['_ROI_Percentage'] = (loan_info['net_return'] / loan_info['loan_amount'] * 100) if loan_info['loan_amount'] > 0 else 0
        
        lender_data.append(lender_row)
    
    # Calculate summary statistics before creating the main table
    print("  Calculating summary statistics...")
    
    # Extract loan amounts and net returns for statistics
    loan_amounts = [abs(row['Loan_Amount']) for row in lender_data if row['Loan_Amount'] is not None]
    net_returns = [row['_Net_Return'] for row in lender_data if row['_Net_Return'] is not None]
    roi_percentages = [row['_ROI_Percentage'] for row in lender_data if row['_ROI_Percentage'] is not None]
    
    # Calculate statistics
    total_rows = len(lender_data)
    positive_returns = sum(1 for nr in net_returns if nr > 0)
    positive_return_pct = (positive_returns / total_rows * 100) if total_rows > 0 else 0
    
    # Calculate IRR for the aggregated cashflow
    def calculate_irr(cashflows):
        """
        Calculate IRR for a series of monthly cashflows.
        """
        try:
            import numpy as np
            import numpy_financial as npf
            
            # Filter out any NaN or infinite values
            cashflows = [cf for cf in cashflows if not (np.isnan(cf) or np.isinf(cf))]
            
            if len(cashflows) < 2:
                return None
            
            # Calculate monthly IRR
            irr_monthly = npf.irr(cashflows)
            
            if irr_monthly is None or np.isnan(irr_monthly) or np.isinf(irr_monthly):
                return None
            
            # Convert to yearly IRR: (1 + monthly_irr)^12 - 1
            irr_yearly = (1 + irr_monthly) ** 12 - 1
            
            return irr_yearly
            
        except Exception as e:
            print(f"    ⚠️  IRR calculation error: {e}")
            return None
    
    # Calculate aggregated cashflow for IRR (sum of all rows)
    aggregated_cashflow = []
    for month in range(1, 61):
        month_sum = sum(row[f'Lender_Cashflow_Month_{month}'] for row in lender_data if f'Lender_Cashflow_Month_{month}' in row)
        aggregated_cashflow.append(month_sum)
    
    # Add initial loan amount (negative) at the beginning
    total_loan_amount = sum(loan_amounts)
    aggregated_cashflow.insert(0, -total_loan_amount)
    
    # Calculate IRR
    irr_yearly = calculate_irr(aggregated_cashflow)
    
    # Calculate loss distribution
    loss_ranges = [
        (0, 10, "0-10%"),
        (10, 20, "10-20%"),
        (20, 30, "20-30%"),
        (30, 40, "30-40%"),
        (40, 50, "40-50%"),
        (50, 60, "50-60%"),
        (60, 70, "60-70%"),
        (70, 80, "70-80%"),
        (80, 90, "80-90%"),
        (90, 100, "90-100%"),
        (100, float('inf'), "100%+")
    ]
    
    loss_distribution = {}
    for min_loss, max_loss, label in loss_ranges:
        if max_loss == float('inf'):
            count = sum(1 for roi in roi_percentages if roi < -min_loss)
        else:
            count = sum(1 for roi in roi_percentages if -max_loss <= roi < -min_loss)
        loss_distribution[label] = (count, count / total_rows * 100) if total_rows > 0 else (0, 0)
    
    # Create main table (remove internal columns)
    main_table_data = []
    for row in lender_data:
        main_row = {}
        for key, value in row.items():
            if not key.startswith('_'):  # Exclude internal columns
                main_row[key] = value
        main_table_data.append(main_row)
    
    # Note: No summary row added - keeping only the original data rows
    
    # Create DataFrame
    lender_df = pd.DataFrame(main_table_data)
    
    # Export to Excel
    print(f"  Exporting to {output_file}...")
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Main data
        lender_df.to_excel(writer, sheet_name='Lender_Cashflow_Simulation', index=False)
        
        # Summary statistics
        summary_data = {
            'Metric': [
                'Total Rows',
                'Total Columns',
                'Loan Amounts',
                'Data Points',
                'Loan Percentage',
                'Yearly Interest Rate',
                'Total Loan Amount',
                'Total Net Return',
                'Positive Return Rate',
                'Loss Distribution (0-10%)',
                'Loss Distribution (10-20%)',
                'Loss Distribution (20-30%)',
                'Loss Distribution (30-40%)',
                'Loss Distribution (40-50%)',
                'Loss Distribution (50-60%)',
                'Loss Distribution (60-70%)',
                'Loss Distribution (70-80%)',
                'Loss Distribution (80-90%)',
                'Loss Distribution (90-100%)',
                'Loss Distribution (100%+)'
            ],
            'Value': [
                len(lender_df),
                len(lender_df.columns),
                len(lender_df['Loan_Amount'].dropna()),
                len(lender_df) * len(lender_df.columns),
                f'{loan_percentage*100:.0f}%',
                f'{yearly_interest_rate*100:.0f}%',
                f'${sum(loan_amounts):,.2f}',
                f'${sum(net_returns):,.2f}',
                f'{positive_return_pct:.2f}%',
                f'{loss_distribution["0-10%"][0]:,} ({loss_distribution["0-10%"][1]:.2f}%)',
                f'{loss_distribution["10-20%"][0]:,} ({loss_distribution["10-20%"][1]:.2f}%)',
                f'{loss_distribution["20-30%"][0]:,} ({loss_distribution["20-30%"][1]:.2f}%)',
                f'{loss_distribution["30-40%"][0]:,} ({loss_distribution["30-40%"][1]:.2f}%)',
                f'{loss_distribution["40-50%"][0]:,} ({loss_distribution["40-50%"][1]:.2f}%)',
                f'{loss_distribution["50-60%"][0]:,} ({loss_distribution["50-60%"][1]:.2f}%)',
                f'{loss_distribution["60-70%"][0]:,} ({loss_distribution["60-70%"][1]:.2f}%)',
                f'{loss_distribution["70-80%"][0]:,} ({loss_distribution["70-80%"][1]:.2f}%)',
                f'{loss_distribution["80-90%"][0]:,} ({loss_distribution["80-90%"][1]:.2f}%)',
                f'{loss_distribution["90-100%"][0]:,} ({loss_distribution["90-100%"][1]:.2f}%)',
                f'{loss_distribution["100%+"][0]:,} ({loss_distribution["100%+"][1]:.2f}%)'
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Sample data
        sample_df = lender_df.head(10)
        sample_df.to_excel(writer, sheet_name='Sample_Data', index=False)
        
        # Column descriptions
        column_descriptions = {
            'Column': [
                'Loan_Amount',
                'Lender_Cashflow_Month_1 through Lender_Cashflow_Month_60'
            ],
            'Description': [
                'Initial loan amount (80% of S&M value, expressed as negative)',
                'Lender cash flows for months 1-60 (80% of gross profit with 16% yearly interest)'
            ],
            'Data Type': [
                'Float (negative value)',
                'Float (lender cash flow values)'
            ]
        }
        desc_df = pd.DataFrame(column_descriptions)
        desc_df.to_excel(writer, sheet_name='Column_Descriptions', index=False)
        
        # Metadata
        metadata = {
            'Parameter': [
                'Table Type',
                'Source File',
                'Lender Cash Flow Calculation',
                'Loan Percentage',
                'Yearly Interest Rate',
                'Total Rows',
                'Total Columns',
                'Data Points',
                'Summary Row',
                'Generated Date'
            ],
            'Value': [
                'Lender Cash Flow Simulation Table',
                input_file,
                'Lender receives 80% of gross profit with 16% yearly interest on outstanding principal',
                f'{loan_percentage*100:.0f}%',
                f'{yearly_interest_rate*100:.0f}%',
                f"{len(lender_df):,}",
                f"{len(lender_df.columns)}",
                f"{len(lender_df) * len(lender_df.columns):,}",
                'Sum of all columns except calculated metrics; Loan metrics calculated from individual rows',
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ]
        }
        metadata_df = pd.DataFrame(metadata)
        metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
    
    print(f"✅ Lender cash flow simulation exported: {output_file}")
    print(f"📋 Sheets included:")
    print(f"  - Lender_Cashflow_Simulation: Main data table ({len(lender_df)} rows x {len(lender_df.columns)} columns)")
    print(f"  - Summary: Dataset statistics with loss distribution")
    print(f"  - Sample_Data: First 10 rows for quick review")
    print(f"  - Column_Descriptions: Explanation of each column")
    print(f"  - Metadata: File information and parameters")
    print(f"📊 Total data points: {len(lender_df) * len(lender_df.columns):,}")
    print(f"💰 Lender cash flow calculation: {loan_percentage*100:.0f}% of gross profit with {yearly_interest_rate*100:.0f}% yearly interest")
    print(f"💡 Total loan amount: ${sum(loan_amounts):,.2f}")
    print(f"📈 Total net return: ${sum(net_returns):,.2f}")
    print(f"📊 Positive return rate: {positive_return_pct:.2f}%")
    print(f"📈 IRR: {irr_yearly*100:.2f}%")
    
    # Return summary statistics
    print(f"Debug: Loss distribution data: {loss_distribution}")
    return {
        'total_loan_amount': sum(loan_amounts),
        'total_net_return': sum(net_returns),
        'positive_return_rate': positive_return_pct,
        'loss_distribution': loss_distribution,
        'irr_yearly': irr_yearly
    }


def create_aggregated_table_from_conservative():
    """
    Create a new table with 1000 rows, each being the sum of 3 random rows from the conservative gross profit simulation.
    """
    import glob
    import random
    
    # Find the conservative file
    conservative_pattern = "gross_profit_simulation_conservative_*.xlsx"
    conservative_files = glob.glob(conservative_pattern)
    
    if not conservative_files:
        print("❌ No conservative gross profit simulation files found.")
        return
    
    # Use the most recent conservative file
    conservative_file = max(conservative_files, key=os.path.getctime)
    print(f"📁 Using conservative file: {conservative_file}")
    
    try:
        # Read the conservative data
        df = pd.read_excel(conservative_file, sheet_name='Gross_Profit_Simulation')
        print(f"✅ Loaded {len(df)} rows from conservative simulation")
        
        # Create aggregated table
        print("🔄 Creating aggregated table with 1000 rows...")
        aggregated_data = []
        
        for i in range(1000):
            if i % 100 == 0:
                print(f"  Processing row {i}/1000...")
            
            # Randomly select 3 rows
            selected_rows = df.sample(n=3, replace=True)
            
            # Sum the selected rows
            aggregated_row = selected_rows.sum(numeric_only=True)
            
            # Remove unwanted columns (LTV to CAC, IRR, and Row ID)
            columns_to_remove = ['LTV_to_CAC', 'IRR', 'Row_ID']
            for col in columns_to_remove:
                if col in aggregated_row:
                    del aggregated_row[col]
            
            aggregated_data.append(aggregated_row)
        
        # Create DataFrame
        aggregated_df = pd.DataFrame(aggregated_data)
        
        # Generate output filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"aggregated_conservative_1000rows_{timestamp}.xlsx"
        
        # Export to Excel
        print(f"📊 Exporting aggregated table to {output_file}...")
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Main aggregated table
            aggregated_df.to_excel(writer, sheet_name='Aggregated_Simulation', index=False)
            
            # Summary statistics
            summary_data = {
                'Metric': [
                    'Total Rows',
                    'Total S&M Value',
                    'Average S&M Value',
                    'Total Gross Profit (All Months)',
                    'Average Gross Profit per Row',
                    'Creation Date',
                    'Source File',
                    'Methodology'
                ],
                'Value': [
                    len(aggregated_df),
                    aggregated_df['SM_Value'].sum(),
                    aggregated_df['SM_Value'].mean(),
                    aggregated_df[[col for col in aggregated_df.columns if 'Gross_Profit_Month_' in col]].sum().sum(),
                    aggregated_df[[col for col in aggregated_df.columns if 'Gross_Profit_Month_' in col]].sum().sum() / len(aggregated_df),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    conservative_file,
                    'Sum of 3 random rows from conservative simulation'
                ]
            }
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Sample data (first 10 rows)
            sample_df = aggregated_df.head(10)
            sample_df.to_excel(writer, sheet_name='Sample_Data', index=False)
            
            # Column descriptions
            descriptions = []
            for col in aggregated_df.columns:
                if col == 'SM_Value':
                    desc = 'Sum of S&M values from 3 randomly selected rows'
                elif 'Gross_Profit_Month_' in col:
                    desc = f'Sum of gross profit values from 3 randomly selected rows for {col}'
                else:
                    desc = f'Sum of {col} values from 3 randomly selected rows'
                descriptions.append({'Column': col, 'Description': desc})
            
            desc_df = pd.DataFrame(descriptions)
            desc_df.to_excel(writer, sheet_name='Column_Descriptions', index=False)
        
        print(f"✅ Aggregated table exported: {output_file}")
        print(f"📋 Sheets included:")
        print(f"  - Aggregated_Simulation: Main data table ({len(aggregated_df)} rows x {len(aggregated_df.columns)} columns)")
        print(f"  - Summary: Dataset statistics")
        print(f"  - Sample_Data: First 10 rows for quick review")
        print(f"  - Column_Descriptions: Explanation of each column")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Error creating aggregated table: {e}")
        return None


def create_aggregated_table_from_less_conservative():
    """
    Create a new table with 1000 rows, each being the sum of 3 random rows from the less conservative gross profit simulation.
    """
    import glob
    import random
    
    # Find the less conservative file
    less_conservative_pattern = "gross_profit_simulation_less_conservative_*.xlsx"
    less_conservative_files = glob.glob(less_conservative_pattern)
    
    if not less_conservative_files:
        print("❌ No less conservative gross profit simulation files found.")
        return
    
    # Use the most recent less conservative file
    less_conservative_file = max(less_conservative_files, key=os.path.getctime)
    print(f"📁 Using less conservative file: {less_conservative_file}")
    
    try:
        # Read the less conservative data
        df = pd.read_excel(less_conservative_file, sheet_name='Gross_Profit_Simulation')
        print(f"✅ Loaded {len(df)} rows from less conservative simulation")
        
        # Create aggregated table
        print("🔄 Creating aggregated table with 1000 rows...")
        aggregated_data = []
        
        for i in range(1000):
            if i % 100 == 0:
                print(f"  Processing row {i}/1000...")
            
            # Randomly select 3 rows
            selected_rows = df.sample(n=3, replace=True)
            
            # Sum the selected rows
            aggregated_row = selected_rows.sum(numeric_only=True)
            
            # Remove unwanted columns (LTV to CAC, IRR, and Row ID)
            columns_to_remove = ['LTV_to_CAC', 'IRR', 'Row_ID']
            for col in columns_to_remove:
                if col in aggregated_row:
                    del aggregated_row[col]
            
            aggregated_data.append(aggregated_row)
        
        # Create DataFrame
        aggregated_df = pd.DataFrame(aggregated_data)
        
        # Generate output filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"aggregated_less_conservative_1000rows_{timestamp}.xlsx"
        
        # Export to Excel
        print(f"📊 Exporting aggregated table to {output_file}...")
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Main aggregated table
            aggregated_df.to_excel(writer, sheet_name='Aggregated_Simulation', index=False)
            
            # Summary statistics
            summary_data = {
                'Metric': [
                    'Total Rows',
                    'Total S&M Value',
                    'Average S&M Value',
                    'Total Gross Profit (All Months)',
                    'Average Gross Profit per Row',
                    'Creation Date',
                    'Source File',
                    'Methodology'
                ],
                'Value': [
                    len(aggregated_df),
                    aggregated_df['SM_Value'].sum(),
                    aggregated_df['SM_Value'].mean(),
                    aggregated_df[[col for col in aggregated_df.columns if 'Gross_Profit_Month_' in col]].sum().sum(),
                    aggregated_df[[col for col in aggregated_df.columns if 'Gross_Profit_Month_' in col]].sum().sum() / len(aggregated_df),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    less_conservative_file,
                    'Sum of 3 random rows from less conservative simulation'
                ]
            }
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Sample data (first 10 rows)
            sample_df = aggregated_df.head(10)
            sample_df.to_excel(writer, sheet_name='Sample_Data', index=False)
            
            # Column descriptions
            descriptions = []
            for col in aggregated_df.columns:
                if col == 'SM_Value':
                    desc = 'Sum of S&M values from 3 randomly selected rows'
                elif 'Gross_Profit_Month_' in col:
                    desc = f'Sum of gross profit values from 3 randomly selected rows for {col}'
                else:
                    desc = f'Sum of {col} values from 3 randomly selected rows'
                descriptions.append({'Column': col, 'Description': desc})
            
            desc_df = pd.DataFrame(descriptions)
            desc_df.to_excel(writer, sheet_name='Column_Descriptions', index=False)
        
        print(f"✅ Aggregated table exported: {output_file}")
        print(f"📋 Sheets included:")
        print(f"  - Aggregated_Simulation: Main data table ({len(aggregated_df)} rows x {len(aggregated_df.columns)} columns)")
        print(f"  - Summary: Dataset statistics")
        print(f"  - Sample_Data: First 10 rows for quick review")
        print(f"  - Column_Descriptions: Explanation of each column")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Error creating aggregated table: {e}")
        return None


def create_summary_table():
    """
    Create a simplified summary table with file titles, sums of first 61 columns, and IRR calculations.
    """
    import glob
    import pandas as pd
    from datetime import datetime
    import os
    import numpy as np
    import numpy_financial as npf
    
    print("📊 Creating simplified summary table with IRR calculations...")
    print(f"🔍 Current working directory: {os.getcwd()}")
    
    # Delete old summary tables first
    old_summary_files = glob.glob("summary_table_*.xlsx")
    if old_summary_files:
        print(f"🗑️  Deleting {len(old_summary_files)} old summary table(s)...")
        for old_file in old_summary_files:
            try:
                os.remove(old_file)
                print(f"  ✅ Deleted: {old_file}")
            except Exception as e:
                print(f"  ⚠️  Could not delete {old_file}: {e}")
    else:
        print("  No old summary tables found to delete")
    
    def calculate_irr(cashflows):
        """
        Calculate IRR for a series of monthly cashflows.
        """
        try:
            # Filter out any NaN or infinite values
            cashflows = [cf for cf in cashflows if not (np.isnan(cf) or np.isinf(cf))]
            
            if len(cashflows) < 2:
                return None
            
            # Calculate monthly IRR
            irr_monthly = npf.irr(cashflows)
            
            if irr_monthly is None or np.isnan(irr_monthly) or np.isinf(irr_monthly):
                return None
            
            # Convert to yearly IRR: (1 + monthly_irr)^12 - 1
            irr_yearly = (1 + irr_monthly) ** 12 - 1
            
            return irr_yearly
            
        except Exception as e:
            print(f"    ⚠️  IRR calculation error: {e}")
            return None
    
    summary_data = []
    
    # Find all simulation files (original)
    simulation_files = glob.glob("gross_profit_simulation_*.xlsx")
    print(f"🔍 Found {len(simulation_files)} simulation files: {simulation_files}")
    
    # Also find aggregated files
    aggregated_files = glob.glob("aggregated_*_1000rows_*.xlsx")
    print(f"🔍 Found {len(aggregated_files)} aggregated files: {aggregated_files}")
    
    # Combine and filter out transformed files
    all_simulation_files = simulation_files + aggregated_files
    all_simulation_files = [f for f in all_simulation_files if 'transformed' not in f]
    all_simulation_files.sort()
    print(f"🔍 Total simulation files to process: {len(all_simulation_files)}")
    
    # Find all transformed files
    transformed_files = glob.glob("*_transformed_*.xlsx")
    transformed_files.sort()
    print(f"🔍 Found {len(transformed_files)} transformed files: {transformed_files}")
    
    # Process original simulation files
    for file_path in all_simulation_files:
        try:
            print(f"  Processing simulation file: {file_path}")
            
            # Try to read from Gross_Profit_Simulation sheet first
            try:
                df = pd.read_excel(file_path, sheet_name='Gross_Profit_Simulation')
            except:
                # If that fails, try Aggregated_Simulation sheet
                df = pd.read_excel(file_path, sheet_name='Aggregated_Simulation')
            
            # Get file title (remove extension and path)
            if 'gross_profit_simulation_' in file_path:
                file_title = file_path.replace('.xlsx', '').replace('gross_profit_simulation_', '')
            elif 'aggregated_' in file_path:
                file_title = file_path.replace('.xlsx', '').replace('aggregated_', '')
            else:
                file_title = file_path.replace('.xlsx', '')
            
            # Calculate sums of first 61 columns (ignore last 2 columns)
            numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns[:61]
            column_sums = []
            for col in numeric_columns:
                column_sums.append(df[col].sum())
            
            # Pad with zeros if less than 61 columns
            while len(column_sums) < 61:
                column_sums.append(0)
            
            # Calculate IRR for the aggregated cashflow (columns B to BJ)
            # First column (A) is the file title, so we use columns 1-60 (B to BJ)
            cashflows = column_sums[:60]  # First 60 columns (B to BJ)
            irr_yearly = calculate_irr(cashflows)
            
            # Create row with file title, column sums, and IRR
            row = [file_title] + column_sums + [irr_yearly if irr_yearly is not None else 0]
            summary_data.append(row)
            
        except Exception as e:
            print(f"  Error processing {file_path}: {e}")
    
    # Process transformed files
    for file_path in transformed_files:
        try:
            print(f"  Processing transformed file: {file_path}")
            
            # Read from Lender_Cashflow_Simulation sheet
            df = pd.read_excel(file_path, sheet_name='Lender_Cashflow_Simulation')
            
            # Get file title (remove extension and path)
            file_title = file_path.replace('.xlsx', '').replace('_transformed_', '_')
            
            # Calculate sums of first 61 columns
            numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns[:61]
            column_sums = []
            for col in numeric_columns:
                column_sums.append(df[col].sum())
            
            # Pad with zeros if less than 61 columns
            while len(column_sums) < 61:
                column_sums.append(0)
            
            # Calculate IRR for the aggregated cashflow (columns B to BJ)
            cashflows = column_sums[:60]  # First 60 columns (B to BJ)
            irr_yearly = calculate_irr(cashflows)
            
            # Create row with file title, column sums, and IRR
            row = [file_title] + column_sums + [irr_yearly if irr_yearly is not None else 0]
            summary_data.append(row)
            
        except Exception as e:
            print(f"  Error processing {file_path}: {e}")
    
    if not summary_data:
        print("❌ No files found to process")
        return None
    
    # Create DataFrame (no header)
    summary_df = pd.DataFrame(summary_data)
    
    # Generate output filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"summary_table_simplified_{timestamp}.xlsx"
    
    # Export to Excel (no header)
    print(f"📊 Exporting simplified summary table with IRR to {output_file}...")
    
    try:
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Main summary table (no header)
            summary_df.to_excel(writer, sheet_name='Summary_Table', index=False, header=False)
            
            # Add a description sheet
            description_data = {
                'Column': ['A', 'B-BJ', 'BK', 'BL'],
                'Description': [
                    'File Title', 
                    'Monthly Cashflow Sums (60 months)', 
                    'Total Sum (61st column)', 
                    'IRR (Yearly)'
                ]
            }
            desc_df = pd.DataFrame(description_data)
            desc_df.to_excel(writer, sheet_name='Column_Descriptions', index=False)
        
        print(f"✅ Simplified summary table with IRR exported: {output_file}")
        print(f"📋 Files processed: {len(summary_data)}")
        print(f"📁 File size: {os.path.getsize(output_file)} bytes")
        print(f"📁 File exists: {os.path.exists(output_file)}")
        print(f"📊 IRR calculations completed for all {len(summary_data)} files")
        
        return output_file
    except Exception as e:
        print(f"❌ Error exporting summary table: {e}")
        return None


def create_and_transform_to_lender_cashflows(loan_percentage=0.80, yearly_interest_rate=0.16):
    """
    Create comprehensive gross profit tables and then transform them to lender cash flows.
    
    Args:
        loan_percentage (float): Percentage of S&M to lend (default 80%)
        yearly_interest_rate (float): Yearly interest rate as decimal (default 16%)
    
    Returns:
        dict: Summary statistics for both conservative and less conservative scenarios
    """
    print("🚀 CREATING COMPREHENSIVE TABLES AND TRANSFORMING TO LENDER CASH FLOWS")
    print("=" * 70)
    
    # Step 0: Clean up any existing files
    print("🧹 Step 0: Cleaning up existing files...")
    import glob
    import os
    
    # Find and delete any existing transformed files
    transformed_pattern = "*_transformed_*.xlsx"
    existing_transformed_files = glob.glob(transformed_pattern)
    if existing_transformed_files:
        print(f"  Found {len(existing_transformed_files)} existing transformed files to delete:")
        for file in existing_transformed_files:
            try:
                os.remove(file)
                print(f"    ✅ Deleted: {file}")
            except Exception as e:
                print(f"    ⚠️  Could not delete {file}: {e}")
    else:
        print("  No existing transformed files found to clean up")
    
    # Find and delete any existing gross profit simulation files
    gross_profit_pattern = "gross_profit_simulation_*.xlsx"
    existing_gross_profit_files = glob.glob(gross_profit_pattern)
    if existing_gross_profit_files:
        print(f"  Found {len(existing_gross_profit_files)} existing gross profit simulation files to delete:")
        for file in existing_gross_profit_files:
            try:
                os.remove(file)
                print(f"    ✅ Deleted: {file}")
            except Exception as e:
                print(f"    ⚠️  Could not delete {file}: {e}")
    else:
        print("  No existing gross profit simulation files found to clean up")
    
    # Find and delete any existing aggregated files
    aggregated_pattern = "aggregated_conservative_1000rows_*.xlsx"
    existing_aggregated_files = glob.glob(aggregated_pattern)
    if existing_aggregated_files:
        print(f"  Found {len(existing_aggregated_files)} existing conservative aggregated files to delete:")
        for file in existing_aggregated_files:
            try:
                os.remove(file)
                print(f"    ✅ Deleted: {file}")
            except Exception as e:
                print(f"    ⚠️  Could not delete {file}: {e}")
    else:
        print("  No existing conservative aggregated files found to clean up")
    
    # Find and delete any existing less conservative aggregated files
    less_conservative_aggregated_pattern = "aggregated_less_conservative_1000rows_*.xlsx"
    existing_less_conservative_aggregated_files = glob.glob(less_conservative_aggregated_pattern)
    if existing_less_conservative_aggregated_files:
        print(f"  Found {len(existing_less_conservative_aggregated_files)} existing less conservative aggregated files to delete:")
        for file in existing_less_conservative_aggregated_files:
            try:
                os.remove(file)
                print(f"    ✅ Deleted: {file}")
            except Exception as e:
                print(f"    ⚠️  Could not delete {file}: {e}")
    else:
        print("  No existing less conservative aggregated files found to clean up")
    
    # Step 1: Create comprehensive tables
    print("\n📊 Step 1: Creating comprehensive gross profit tables...")
    create_comprehensive_table()
    
    # Step 1.5: Create aggregated table from conservative data
    print("\n📊 Step 1.5: Creating aggregated table from conservative data...")
    create_aggregated_table_from_conservative()
    
    # Step 1.6: Create aggregated table from less conservative data
    print("\n📊 Step 1.6: Creating aggregated table from less conservative data...")
    create_aggregated_table_from_less_conservative()
    
    # Step 2: Find the generated files and transform them
    print("\n📊 Step 2: Transforming gross profit tables to lender cash flows...")
    
    import glob
    
    # Find all files to transform (gross profit and aggregated)
    gross_profit_pattern = "gross_profit_simulation_*.xlsx"
    aggregated_pattern = "aggregated_*_1000rows_*.xlsx"
    
    gross_profit_files = glob.glob(gross_profit_pattern)
    aggregated_files = glob.glob(aggregated_pattern)
    
    files = gross_profit_files + aggregated_files
    
    if not files:
        print("❌ No files found to transform. Please run create_comprehensive_table.py first.")
        return
    
    print(f"Found {len(files)} files to transform:")
    for i, file in enumerate(files, 1):
        print(f"  {i}. {file}")
    
    # Debug: Check if both scenarios are present
    conservative_files = [f for f in files if 'conservative' in f.lower() and 'less' not in f.lower()]
    less_conservative_files = [f for f in files if 'less_conservative' in f.lower()]
    
    print(f"Debug: Found {len(conservative_files)} conservative files: {conservative_files}")
    print(f"Debug: Found {len(less_conservative_files)} less conservative files: {less_conservative_files}")
    
    print(f"\nTransforming all files with {loan_percentage*100:.0f}% loan and {yearly_interest_rate*100:.0f}% yearly interest...")
    
    # Transform each file and collect results
    results = {}
    for file in files:
        print(f"\n🔄 Transforming {file} to lender cash flows...")
        
        # Generate output filename
        base_name = os.path.splitext(file)[0]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"{base_name}_transformed_{timestamp}.xlsx"
        
        # Transform the file and get results
        result = transform_gross_profit_to_lender_cashflows(file, output_file, loan_percentage, yearly_interest_rate)
        
        # Determine scenario type from filename
        if 'conservative' in file.lower() and 'less' not in file.lower():
            scenario = 'conservative'
        else:
            scenario = 'less_conservative'
        
        # Add file type identifier
        if 'aggregated' in file.lower():
            file_type = 'aggregated'
        else:
            file_type = 'original'
        
        scenario_key = f"{scenario}_{file_type}"
        
        print(f"Debug: File '{file}' mapped to scenario '{scenario_key}'")
        results[scenario_key] = result
        
        print("=" * 60)
    
    print("\n✅ All files created and transformed successfully!")
    
    # Step 4: Create summary table with column totals for all 8 files
    print("\n🔄 Step 4: Creating summary table with column totals...")
    summary_file = create_summary_table()
    if summary_file:
        print(f"✅ Summary table created: {summary_file}")
    else:
        print("⚠️  Summary table creation failed")
    
    return results


def batch_transform_gross_profit_files(pattern="gross_profit_simulation_*.xlsx", loan_percentage=0.80, yearly_interest_rate=0.16):
    """
    Transform all gross profit simulation files matching the pattern.
    
    Args:
        pattern (str): File pattern to match (default: "gross_profit_simulation_*.xlsx")
        loan_percentage (float): Percentage of S&M to lend (default 80%)
        yearly_interest_rate (float): Yearly interest rate as decimal (default 16%)
    """
    import glob
    
    files = glob.glob(pattern)
    if not files:
        print(f"No files found matching pattern: {pattern}")
        return
    
    print(f"Found {len(files)} files to transform:")
    for file in files:
        print(f"  - {file}")
    
    for file in files:
        # Create output filename
        output_file = file.replace('gross_profit_simulation_', 'lender_cashflow_simulation_')
        output_file = output_file.replace('.xlsx', f'_transformed_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')
        
        print(f"\n{'='*60}")
        transform_gross_profit_to_lender_cashflows(file, output_file, loan_percentage, yearly_interest_rate)


if __name__ == "__main__":
    # Use the new function that creates comprehensive tables first
    create_and_transform_to_lender_cashflows() 