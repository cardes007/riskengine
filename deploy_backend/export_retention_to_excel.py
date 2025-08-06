import json
import pandas as pd

def export_retention_to_excel():
    with open('full_cohort_data.json', 'r') as f:
        cohorts_data = json.load(f)
    
    # Build the retention table
    retention_rows = []
    cohort_names = []
    num_months = len(cohorts_data[0]['revenue_array'])
    for cohort in cohorts_data:
        cohort_names.append(cohort['cohort_name'])
        rev = cohort['revenue_array']
        row = []
        for i in range(1, len(rev)):
            prev = rev[i-1]
            curr = rev[i]
            if prev > 0:
                rate = curr / prev
                row.append(rate)
            else:
                row.append(None)
        retention_rows.append(row)
    
    # Fix the diagonal issue: replace rightmost 0s and diagonal with None
    for row_idx in range(2, len(retention_rows)):  # Start from row 3 (index 2)
        row = retention_rows[row_idx]
        # Find the rightmost non-None value
        rightmost_idx = len(row) - 1
        while rightmost_idx >= 0 and row[rightmost_idx] is None:
            rightmost_idx -= 1
        
        # If the rightmost value is 0, replace it and the diagonal with None
        if rightmost_idx >= 0 and row[rightmost_idx] == 0:
            # Replace the 0 and all values to its right with None
            for col_idx in range(rightmost_idx, len(row)):
                row[col_idx] = None
            
        
    
    # Create DataFrame
    month_headers = [f"M{i+1}" for i in range(1, num_months)]
    df = pd.DataFrame(retention_rows, columns=month_headers, index=cohort_names)
    # Format as percentage (Excel will show as 0.95 for 95%, so multiply by 100 and set format)
    df_percent = df.map(lambda x: x*100 if x is not None else None)
    # Export to Excel
    output_file = "retention_table.xlsx"
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        df_percent.to_excel(writer, sheet_name='Retention')
        # Set percentage format
        workbook  = writer.book
        worksheet = writer.sheets['Retention']
        percent_fmt = workbook.add_format({'num_format': '0.0%'})
        for col_num, value in enumerate(df_percent.columns.values):
            worksheet.set_column(col_num+1, col_num+1, 10, percent_fmt)
    print(f"Retention table exported to {output_file}")

if __name__ == "__main__":
    export_retention_to_excel() 