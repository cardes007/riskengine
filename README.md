# Company Cohort Web Application

A comprehensive web application for analyzing company P&L statements and revenue cohorts with Python backend integration.

## Features

### Frontend (React)
- **P&L Statement Input**: Interactive form for entering monthly P&L data
- **Revenue Cohorts**: Cohort analysis with retention tracking
- **Net Dollar Retention (NDR) Analysis**: Comprehensive NDR tables and charts
- **Cohort Payback Analysis**: Payback period calculations and visualizations
- **Unit Economics**: S&M spend analysis and CAC calculations
- **Quarterly Analysis**: Quarterly cohort and payback analysis
- **Backend Integration**: Direct integration with Python backend for data processing

### Backend (Python FastAPI)
- **S&M Data Import**: Extract and process Sales & Marketing data from P&L
- **Revenue Cohorts Import**: Process first column of Revenue Cohorts data
- **RESTful API**: Clean API endpoints with proper error handling
- **CORS Support**: Configured for frontend integration
- **Data Validation**: Robust data validation and error handling

## Quick Start

### Option 1: Use the startup script (Recommended)
```bash
./start.sh
```

### Option 2: Manual setup

1. **Install Frontend Dependencies**
```bash
npm install
```

2. **Install Backend Dependencies**
```bash
cd backend
pip install -r requirements.txt
cd ..
```

3. **Start the Backend**
```bash
cd backend
python main.py
```

4. **Start the Frontend** (in a new terminal)
```bash
npm run dev
```

## Usage

### Frontend
1. Open `http://localhost:5173` in your browser
2. Enter P&L data in the first form
3. Enter Revenue Cohorts data in the second form
4. Use the "Backend Integration" section to import data to Python backend
5. Click "Analyze Data" to view comprehensive analysis

### Backend API
The backend provides the following endpoints:

- `GET /health` - Health check
- `POST /import/sm-data` - Import S&M data only
- `POST /import/revenue-cohorts` - Import Revenue Cohorts data only
- `POST /import/all` - Import both S&M and Revenue Cohorts data

### API Documentation
Once the backend is running, view the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Data Structure

### P&L Data Format
```json
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
```

### Revenue Cohorts Data Format
```json
{
  "name": "Jan 24",
  "revenue": ["300000", "250000", "200000"]
}
```

## Analysis Features

### Net Dollar Retention (NDR)
- Individual cohort NDR calculations
- Simple, weighted, and median averages
- Yearly weighted averages
- Forecast curves and conservative forecasts
- Interactive line charts

### Cohort Payback
- Monthly and quarterly payback analysis
- Gross profit cohort calculations
- Payback period highlighting
- Interactive payback charts

### Unit Economics
- S&M spend per new revenue
- Rolling averages (3-month)
- Statistical analysis (min, max, mean, median, std dev)
- Histogram visualization
- Yearly and marginal CAC analysis

## Testing

### Backend Testing
```bash
cd backend
python test_api.py
```

### Frontend Testing
```bash
npm test
```

## Project Structure

```
company-cohort-web/
├── src/
│   ├── components/
│   │   ├── PLForm.jsx              # P&L input form
│   │   ├── CohortForm.jsx          # Revenue cohorts form
│   │   └── BackendIntegration.jsx  # Backend integration component
│   ├── App.jsx                     # Main application
│   └── main.jsx                    # React entry point
├── backend/
│   ├── main.py                     # FastAPI application
│   ├── test_api.py                 # API testing script
│   ├── requirements.txt            # Python dependencies
│   └── README.md                   # Backend documentation
├── start.sh                        # Startup script
└── README.md                       # This file
```

## Development

### Frontend Development
- Built with React and Vite
- Uses localStorage for data persistence
- Responsive design with modern CSS
- Interactive charts and visualizations

### Backend Development
- Built with FastAPI
- Pydantic models for data validation
- CORS configured for frontend integration
- Comprehensive error handling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.
# company-cohort-web
# riskengine
