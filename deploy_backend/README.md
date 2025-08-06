# Company Cohort Web Backend

A Python FastAPI backend for importing and processing P&L and Revenue Cohorts data.

## Features

- Import S&M (Sales & Marketing) data from P&L statements
- Import first column of Revenue Cohorts data
- RESTful API endpoints with proper error handling
- CORS enabled for frontend integration

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Health Check
- `GET /health` - Check if the API is running

### Import Endpoints

#### Import S&M Data Only
- `POST /import/sm-data` - Extract S&M values from P&L data

#### Import Revenue Cohorts Data Only
- `POST /import/revenue-cohorts` - Extract first column of Revenue Cohorts data

#### Import All Data
- `POST /import/all` - Import both S&M and Revenue Cohorts data

## Data Format

### Request Format
```json
{
  "pl_data": [
    {
      "month": "Jan 24",
      "revenue": "1000000",
      "cogs": "400000",
      "grossProfit": "600000",
      "opex": "300000",
      "sm": "150000",
      "rd": "100000",
      "ga": "50000",
      "ebitda": "300000",
      "taxes": "60000",
      "interest": "10000",
      "da": "20000",
      "netIncome": "210000"
    }
  ],
  "cohort_data": [
    {
      "name": "Older Cohorts",
      "revenue": ["500000", "450000", "400000"]
    },
    {
      "name": "Jan 24",
      "revenue": ["300000", "250000", "200000"]
    }
  ]
}
```

### Response Format

#### S&M Data Response
```json
{
  "success": true,
  "sm_data": [
    {
      "month": "Jan 24",
      "sm_value": 150000.0
    }
  ],
  "count": 1
}
```

#### Revenue Cohorts Response
```json
{
  "success": true,
  "cohort_data": [
    {
      "cohort_name": "Older Cohorts",
      "first_month_revenue": 500000.0
    }
  ],
  "count": 1
}
```

## Testing

Run the test script to verify the API:
```bash
python test_api.py
```

## API Documentation

Once the server is running, you can view the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc` 