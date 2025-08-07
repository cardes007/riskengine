from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
import os

app = FastAPI(title="Risk Engine Backend", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for deployed version
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Data models
class PLDataRow(BaseModel):
    month: str
    revenue: str = ""
    cogs: str = ""
    grossProfit: str = ""
    opex: str = ""
    sm: str = ""
    rd: str = ""
    ga: str = ""
    ebitda: str = ""
    taxes: str = ""
    interest: str = ""
    da: str = ""
    netIncome: str = ""

class CohortDataRow(BaseModel):
    name: str
    revenue: List[str]

class ImportData(BaseModel):
    pl_data: List[PLDataRow]
    cohort_data: List[CohortDataRow]

class SMData(BaseModel):
    month: str
    sm_value: float

class RevenueCohortData(BaseModel):
    cohort_name: str
    first_month_revenue: float

class FullRevenueCohortData(BaseModel):
    cohort_name: str
    revenue_array: List[float]
    month: str

class TransformRequest(BaseModel):
    yearly_interest_rate: float = 0.16

@app.get("/")
async def root():
    return {"message": "Risk Engine Backend API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.options("/import/all")
async def import_all_options():
    """
    Handle OPTIONS request for CORS preflight
    """
    return {"message": "OK"}

@app.get("/import/all")
async def import_all_get():
    """
    GET endpoint for debugging import path
    """
    return {"message": "Import endpoint accessible via GET", "status": "ok"}

@app.post("/test-import")
async def test_import():
    """
    Simple test endpoint to verify POST requests work
    """
    return {"message": "POST request successful", "status": "ok"}

@app.exception_handler(405)
async def method_not_allowed_handler(request, exc):
    """
    Handle 405 Method Not Allowed errors
    """
    print(f"🚨 405 Error: {request.method} {request.url}")
    print(f"🚨 Allowed methods: {request.scope.get('allowed_methods', [])}")
    return {"error": "Method not allowed", "method": request.method, "url": str(request.url), "status": 405}

@app.get("/ndr-evolution")
async def get_ndr_evolution():
    """
    Get NDR evolution data for frontend visualization
    """
    try:
        from calculate_ndr import calculate_ndr_evolution
        import io
        import sys
        
        # Capture the output from calculate_ndr_evolution
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        # Import the function and get the data
        with open('full_cohort_data.json', 'r') as f:
            cohorts_data = json.load(f)
        
        num_months = len(cohorts_data[0]['revenue_array'])
        if num_months < 13:
            return {"error": "Not enough months of data to calculate NDR (need at least 13)."}
        
        ndr_evolution = []
        month_labels = [f"M{i+1}" for i in range(num_months)]
        
        # For each possible ending month (from col 12 to last col - chronological order)
        for end_col in range(12, num_months):
            numerator = 0.0
            denominator = 0.0
            row = 0
            col = end_col
            # Step 1: Add last value of first row
            cohort = cohorts_data[row]
            revenue_array = cohort['revenue_array']
            retained_value = revenue_array[col]
            numerator += retained_value
            base_col = col - 12
            base_value = revenue_array[base_col]
            denominator += base_value
            # Step 2: Add last value of second row
            row = 1
            col = end_col
            if row < len(cohorts_data):
                cohort = cohorts_data[row]
                revenue_array = cohort['revenue_array']
                retained_value = revenue_array[col]
                numerator += retained_value
                base_col = col - 12
                base_value = revenue_array[base_col]
                denominator += base_value
            # Step 3: For subsequent cohorts, move diagonally down and left
            row = 2
            col = end_col - 1
            while row < len(cohorts_data) and col >= 12:
                cohort = cohorts_data[row]
                revenue_array = cohort['revenue_array']
                retained_value = revenue_array[col]
                numerator += retained_value
                base_col = col - 12
                base_value = revenue_array[base_col]
                denominator += base_value
                row += 1
                col -= 1
            ndr = numerator / denominator if denominator > 0 else None
            ndr_evolution.append({
                "month": month_labels[end_col],
                "ndr": ndr,
                "ndr_percentage": ndr * 100 if ndr is not None else None
            })
        
        # Restore stdout
        sys.stdout = sys.__stdout__
        
        # Reverse the array to get chronological order (M13 first, M24 last)
        ndr_evolution.reverse()
        
        # Calculate statistics
        ndr_values = [ndr for item in ndr_evolution if item['ndr'] is not None]
        if ndr_values:
            import statistics
            median_ndr = statistics.median(ndr_values)
            monthly_retention = median_ndr ** (1/12)
            stats = {
                "median_ndr": median_ndr,
                "median_ndr_percentage": median_ndr * 100,
                "monthly_retention": monthly_retention,
                "monthly_retention_percentage": monthly_retention * 100
            }
        else:
            stats = None
        
        return {
            "success": True,
            "ndr_evolution": ndr_evolution,
            "statistics": stats,
            "total_months": len(ndr_evolution)
        }
        
    except Exception as e:
        return {"error": f"Error calculating NDR evolution: {str(e)}"}

@app.post("/import/sm-data")
async def import_sm_data(data: ImportData):
    """
    Extract S&M data from P&L inputs
    """
    try:
        sm_data = []
        for row in data.pl_data:
            if row.sm and row.sm.strip():
                try:
                    sm_value = float(row.sm.replace(',', '').replace('$', ''))
                    sm_data.append(SMData(
                        month=row.month,
                        sm_value=sm_value
                    ))
                except ValueError:
                    # Skip invalid values
                    continue
        
        return {
            "success": True,
            "sm_data": sm_data,
            "count": len(sm_data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing S&M data: {str(e)}")

@app.post("/import/revenue-cohorts")
async def import_revenue_cohorts(data: ImportData):
    """
    Extract first column of Revenue Cohorts data
    """
    try:
        cohort_data = []
        for cohort in data.cohort_data:
            if cohort.revenue and len(cohort.revenue) > 0:
                first_revenue = cohort.revenue[0]
                if first_revenue and first_revenue.strip():
                    try:
                        revenue_value = float(first_revenue.replace(',', '').replace('$', ''))
                        cohort_data.append(RevenueCohortData(
                            cohort_name=cohort.name,
                            first_month_revenue=revenue_value
                        ))
                    except ValueError:
                        # Skip invalid values
                        continue
        
        return {
            "success": True,
            "cohort_data": cohort_data,
            "count": len(cohort_data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing cohort data: {str(e)}")

@app.post("/import/full-cohorts")
async def import_full_cohorts(data: ImportData):
    """
    Import the entire Revenue Cohorts data table
    """
    print("\n" + "="*60)
    print("🚀 IMPORTING FULL REVENUE COHORTS DATA")
    print("="*60)
    
    try:
        print(f"📊 Received {len(data.cohort_data)} cohort rows")
        
        full_cohort_data = []
        
        for cohort in data.cohort_data:
            # Convert all revenue values to floats, keeping the original array structure
            revenue_array = []
            for revenue_str in cohort.revenue:
                if revenue_str and revenue_str.strip():
                    try:
                        revenue_value = float(revenue_str.replace(',', '').replace('$', ''))
                        revenue_array.append(revenue_value)
                    except ValueError:
                        revenue_array.append(0.0)
                else:
                    revenue_array.append(0.0)
            
            full_cohort_data.append(FullRevenueCohortData(
                cohort_name=cohort.name,
                revenue_array=revenue_array,
                month=cohort.name
            ))
        
        print(f"💰 Processed {len(full_cohort_data)} cohorts with revenue arrays")
        
        # Save full cohort data to JSON file
        try:
            with open('full_cohort_data.json', 'w') as f:
                json.dump([{
                    "cohort_name": item.cohort_name,
                    "revenue_array": item.revenue_array,
                    "month": item.month
                } for item in full_cohort_data], f, indent=2)
            print(f"💾 Full cohort data saved to full_cohort_data.json")
        except Exception as save_error:
            print(f"⚠️ Warning: Could not save full cohort data: {save_error}")
        
        print("="*60)
        print("✅ FULL COHORT IMPORT COMPLETED SUCCESSFULLY")
        print("="*60 + "\n")
        
        return {
            "success": True,
            "full_cohort_data": {
                "data": full_cohort_data,
                "count": len(full_cohort_data)
            }
        }
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print("="*60 + "\n")
        raise HTTPException(status_code=500, detail=f"Error processing full cohort data: {str(e)}")

@app.post("/import/all")
async def import_all_data(data: ImportData):
    """
    Import both S&M data and Revenue Cohorts first column data
    """
    print("\n" + "="*60)
    print("🚀 IMPORTING DATA FROM FRONTEND")
    print("="*60)
    print(f"📋 Request method: POST")
    print(f"📋 Data received: {type(data)}")
    print(f"📋 P&L data count: {len(data.pl_data) if data.pl_data else 0}")
    print(f"📋 Cohort data count: {len(data.cohort_data) if data.cohort_data else 0}")
    
    try:
        print(f"📊 Received {len(data.pl_data) if data.pl_data else 0} P&L rows and {len(data.cohort_data) if data.cohort_data else 0} cohort rows")
        
        # Validate input data
        if not data.pl_data:
            print("⚠️  No P&L data received")
            return {"error": "No P&L data provided", "status": "error"}
        
        if not data.cohort_data:
            print("⚠️  No cohort data received")
            return {"error": "No cohort data provided", "status": "error"}
        
        print(f"✅ Data validation passed")
        print(f"✅ P&L data type: {type(data.pl_data)}")
        print(f"✅ Cohort data type: {type(data.cohort_data)}")
        
        # Extract S&M data
        sm_data = []
        print("\n📈 Processing S&M data from P&L:")
        for i, row in enumerate(data.pl_data, 1):
            print(f"  Row {i}: Month = '{row.month}', S&M = '{row.sm}'")
            if row.sm and row.sm.strip():
                try:
                    sm_value = float(row.sm.replace(',', '').replace('$', ''))
                    sm_data.append(SMData(
                        month=row.month,
                        sm_value=sm_value
                    ))
                    print(f"    ✅ Extracted: ${sm_value:,.2f}")
                except ValueError:
                    print(f"    ❌ Invalid value: '{row.sm}'")
                    continue
            else:
                print(f"    ⚠️  Empty S&M value")
        
        # Extract Revenue Cohorts first column data
        cohort_data = []
        print("\n📊 Processing Revenue Cohorts data:")
        for i, cohort in enumerate(data.cohort_data, 1):
            print(f"  Cohort {i}: Name = '{cohort.name}', Revenue array = {cohort.revenue}")
            if cohort.revenue and len(cohort.revenue) > 0:
                first_revenue = cohort.revenue[0]
                print(f"    First revenue value: '{first_revenue}'")
                if first_revenue and first_revenue.strip():
                    try:
                        revenue_value = float(first_revenue.replace(',', '').replace('$', ''))
                        cohort_data.append(RevenueCohortData(
                            cohort_name=cohort.name,
                            first_month_revenue=revenue_value
                        ))
                        print(f"    ✅ Extracted: ${revenue_value:,.2f}")
                    except ValueError:
                        print(f"    ❌ Invalid value: '{first_revenue}'")
                        continue
                else:
                    print(f"    ⚠️  Empty first revenue value")
            else:
                print(f"    ⚠️  No revenue data")
        
        print(f"\n💰 SUMMARY:")
        print(f"  S&M records extracted: {len(sm_data)}")
        print(f"  Cohort records extracted: {len(cohort_data)}")
        
        # Create full cohort data for prediction engine
        full_cohort_data = []
        print("\n📊 Creating full cohort data:")
        for i, cohort in enumerate(data.cohort_data, 1):
            print(f"  Processing cohort {i}: {cohort.name}")
            # Convert all revenue values to floats, keeping the original array structure
            revenue_array = []
            for revenue_str in cohort.revenue:
                if revenue_str and revenue_str.strip():
                    try:
                        revenue_value = float(revenue_str.replace(',', '').replace('$', ''))
                        revenue_array.append(revenue_value)
                    except ValueError:
                        revenue_array.append(0.0)
                else:
                    revenue_array.append(0.0)
            
            full_cohort_data.append(FullRevenueCohortData(
                cohort_name=cohort.name,
                revenue_array=revenue_array,
                month=cohort.name
            ))
            print(f"    ✅ Added {len(revenue_array)} revenue values")
        
        print(f"  💾 Created {len(full_cohort_data)} full cohort records")
        
        # Save data to JSON files for the viewer script
        try:
            with open('sm_data.json', 'w') as f:
                json.dump([{"month": item.month, "sm_value": item.sm_value} for item in sm_data], f, indent=2)
            print(f"  💾 S&M data saved to sm_data.json")
            
            with open('cohort_data.json', 'w') as f:
                json.dump([{"cohort_name": item.cohort_name, "first_month_revenue": item.first_month_revenue, "month": item.cohort_name} for item in cohort_data], f, indent=2)
            print(f"  💾 Cohort data saved to cohort_data.json")
            
            with open('full_cohort_data.json', 'w') as f:
                json.dump([{
                    "cohort_name": item.cohort_name,
                    "revenue_array": item.revenue_array,
                    "month": item.month
                } for item in full_cohort_data], f, indent=2)
            print(f"  💾 Full cohort data saved to full_cohort_data.json")
            
            # Save P&L data for gross margin calculations
            pl_data = []
            for row in data.pl_data:
                pl_row = {
                    "month": row.month,
                    "revenue": row.revenue,
                    "cogs": row.cogs,
                    "grossProfit": row.grossProfit,
                    "opex": row.opex,
                    "sm": row.sm,
                    "rd": row.rd,
                    "ga": row.ga,
                    "ebitda": row.ebitda,
                    "taxes": row.taxes,
                    "interest": row.interest,
                    "da": row.da,
                    "netIncome": row.netIncome
                }
                pl_data.append(pl_row)
            
            with open('pl_data.json', 'w') as f:
                json.dump(pl_data, f, indent=2)
            print(f"  💾 P&L data saved to pl_data.json for gross margin calculations")
            
        except Exception as save_error:
            print(f"  ⚠️  Warning: Could not save data files: {save_error}")
        
        print("="*60)
        print("✅ IMPORT COMPLETED SUCCESSFULLY")
        print("="*60 + "\n")
        
        return {
            "success": True,
            "sm_data": {
                "data": sm_data,
                "count": len(sm_data)
            },
            "cohort_data": {
                "data": cohort_data,
                "count": len(cohort_data)
            },
            "full_cohort_data": {
                "data": full_cohort_data,
                "count": len(full_cohort_data)
            },
            "pl_data": {
                "count": len(pl_data)
            }
        }
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print("="*60 + "\n")
        raise HTTPException(status_code=500, detail=f"Error processing data: {str(e)}")

@app.post("/transform-to-lender-cashflows")
async def transform_to_lender_cashflows(request: TransformRequest):
    """
    Run the transform_to_lender_cashflows.py script to create lender cash flow simulations
    """
    try:
        print("\n" + "="*60)
        print("🚀 TRANSFORMING TO LENDER CASH FLOWS")
        print("="*60)
        print(f"📊 Using yearly interest rate: {request.yearly_interest_rate*100:.1f}%")
        
        # Import and run the transform function
        from transform_to_lender_cashflows import create_and_transform_to_lender_cashflows
        
        # Run the transformation and get results
        results = create_and_transform_to_lender_cashflows(yearly_interest_rate=request.yearly_interest_rate)
        
        print("="*60)
        print("✅ LENDER CASH FLOW TRANSFORMATION COMPLETED")
        print("="*60 + "\n")
        
        return {
            "success": True,
            "message": f"Lender cash flow transformation completed successfully with {request.yearly_interest_rate*100:.1f}% yearly interest rate",
            "files_created": "Check the backend directory for the generated Excel files",
            "results": results
        }
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print("="*60 + "\n")
        raise HTTPException(status_code=500, detail=f"Error running lender cash flow transformation: {str(e)}")

@app.get("/get-irr-data")
async def get_irr_data():
    """
    Get IRR data from summary table files
    """
    try:
        import glob
        import pandas as pd
        import os
        
        # Find all summary table files
        summary_files = glob.glob("summary_table_simplified_*.xlsx")
        
        if not summary_files:
            return {
                "files": [],
                "message": "No summary table files found. Please run the Risk Analysis first."
            }
        
        irr_data = []
        
        for file_path in summary_files:
            try:
                # Read the Excel file
                df = pd.read_excel(file_path)
                
                # Get the IRR values from the rightmost column for each row
                if len(df.columns) > 0:
                    irr_column = df.columns[-1]
                    
                    # Extract IRR values for each row (each file)
                    for index, row in df.iterrows():
                        file_name = row.iloc[0]  # First column contains file names
                        irr_value = row.iloc[-1]  # Last column contains IRR values
                        
                        # Convert to float if it's a valid number
                        if pd.notna(irr_value) and isinstance(irr_value, (int, float)):
                            irr_value = float(irr_value)
                        else:
                            irr_value = None
                        
                        irr_data.append({
                            "name": str(file_name),
                            "irr": irr_value
                        })
                else:
                    irr_data.append({
                        "name": os.path.basename(file_path),
                        "irr": None
                    })
                    
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")
                irr_data.append({
                    "name": os.path.basename(file_path),
                    "irr": None
                })
        
        return {
            "files": irr_data,
            "message": f"Found {len(irr_data)} summary table files"
        }
        
    except Exception as e:
        print(f"Error getting IRR data: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting IRR data: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 