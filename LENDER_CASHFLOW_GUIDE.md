# Lender Cashflow Transform Guide

This guide explains how to use the new lender cashflow transform functionality in the Company Cohort Web application.

## Overview

The lender cashflow transform feature allows you to convert gross profit simulation data into lender cash flow simulations. This is useful for analyzing how a lender would perform when providing loans based on a company's gross profit data.

## How It Works

1. **Data Import**: First, import your P&L data and revenue cohorts through the frontend
2. **Transform**: Click the "Transform to Lender Cashflows" button to run the transformation
3. **Output**: The system generates Excel files with lender cash flow simulations

## Step-by-Step Instructions

### 1. Start the Application

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

cd ..
npm install

# Start both servers
./start.sh
```

### 2. Import Your Data

1. Open the frontend at `http://localhost:5173`
2. Fill in your P&L data and revenue cohorts
3. Click the **"Import Data"** button in the Backend Integration section
4. Wait for the import to complete (you'll see a success message)

### 3. Transform to Lender Cashflows

1. Once the data is imported successfully, the **"Transform to Lender Cashflows"** button will become enabled
2. Click the **"Transform to Lender Cashflows"** button
3. Wait for the transformation to complete (this may take a few minutes depending on data size)
4. You'll see a success message when complete

### 4. Find Your Results

The generated Excel files will be saved in the `backend/` directory with names like:
- `gross_profit_simulation_conservative_YYYYMMDD_HHMMSS_transformed_YYYYMMDD_HHMMSS.xlsx`
- `gross_profit_simulation_less_conservative_YYYYMMDD_HHMMSS_transformed_YYYYMMDD_HHMMSS.xlsx`

## What the Transformation Does

The transformation process:

1. **Creates Comprehensive Tables**: First generates gross profit simulation tables from your data
2. **Applies Lender Logic**: Converts gross profit data to lender cash flows using:
   - **Loan Percentage**: 80% of S&M value (configurable)
   - **Interest Rate**: 16% yearly interest (configurable)
3. **Generates Excel Files**: Creates detailed Excel files with multiple sheets:
   - **Lender_Cashflow_Simulation**: Main data table
   - **Summary**: Dataset statistics and loss distribution
   - **Sample_Data**: First 10 rows for quick review
   - **Column_Descriptions**: Explanation of each column
   - **Metadata**: File information and parameters

## Excel File Contents

### Lender_Cashflow_Simulation Sheet
- **Loan_Amount**: Initial loan amount (80% of S&M value, expressed as negative)
- **Lender_Cashflow_Month_1 through Lender_Cashflow_Month_60**: Lender cash flows for months 1-60

### Summary Sheet
- Total rows and columns
- Loan amounts and data points
- Loan percentage and interest rate
- Total loan amount and net return
- Positive return rate
- Loss distribution across different ranges

## Technical Details

### Backend Endpoint
- **URL**: `POST /transform-to-lender-cashflows`
- **Function**: Runs the `transform_to_lender_cashflows.py` script
- **Dependencies**: Requires pandas, numpy, and openpyxl

### Parameters (Configurable)
- **Loan Percentage**: Default 80% (0.80)
- **Yearly Interest Rate**: Default 16% (0.16)

## Troubleshooting

### Common Issues

1. **Button Not Enabled**: Make sure you've successfully imported data first
2. **Transformation Fails**: Check that you have sufficient data (at least 12 months of cohort data)
3. **Files Not Generated**: Check the backend console for error messages

### Testing

You can test the functionality using the provided test script:

```bash
python test_lender_transform.py
```

This will test all the backend endpoints and verify the transformation works correctly.

## File Structure

```
backend/
├── transform_to_lender_cashflows.py    # Main transformation script
├── lender_cashflow_calculator.py       # Core calculation logic
├── create_comprehensive_table.py       # Table generation
└── [generated Excel files]             # Output files
```

## Next Steps

After generating the lender cashflow files, you can:
1. Analyze the loss distribution to understand risk
2. Review the positive return rate
3. Examine individual lender cash flow scenarios
4. Use the data for further financial modeling

For questions or issues, check the backend console output for detailed logging information. 