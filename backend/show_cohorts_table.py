import json
from datetime import datetime

def format_currency(value):
    """Format number as currency"""
    if value == 0:
        return "-"
    return f"${value:,.0f}"

def show_cohorts_table():
    """Display the full cohorts data as a formatted table"""
    print("📊 FULL REVENUE COHORTS DATA TABLE")
    print("=" * 120)
    
    # Load the data
    with open('full_cohort_data.json', 'r') as f:
        cohorts_data = json.load(f)
    
    # Create month headers
    month_headers = [f"M{i+1}" for i in range(24)]
    
    # Print header row
    header = f"{'Cohort':<15} " + " ".join([f"{month:>8}" for month in month_headers])
    print(header)
    print("-" * 120)
    
    # Print each cohort row
    for cohort in cohorts_data:
        cohort_name = cohort['cohort_name']
        revenue_array = cohort['revenue_array']
        
        # Format the revenue values
        formatted_revenues = [format_currency(value) for value in revenue_array]
        
        # Create the row
        row = f"{cohort_name:<15} " + " ".join([f"{value:>8}" for value in formatted_revenues])
        print(row)
    
    print("-" * 120)
    print(f"Total Cohorts: {len(cohorts_data)}")
    print(f"Data exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 120)

if __name__ == "__main__":
    show_cohorts_table() 