import json
import os

def load_and_print_data():
    print("📊 DATA VIEWER - Company Cohort Web Backend")
    print("=" * 50)
    
    sm_file = 'sm_data.json'
    cohort_file = 'cohort_data.json'
    
    if not os.path.exists(sm_file):
        print(f"❌ {sm_file} not found. Please import data first.")
        return
    
    if not os.path.exists(cohort_file):
        print(f"❌ {cohort_file} not found. Please import data first.")
        return
    
    print("✅ Found data files")
    print()
    
    # Load S&M data
    try:
        with open(sm_file, 'r') as f:
            sm_data = json.load(f)
        print(f"📈 S&M DATA ({len(sm_data)} records):")
        print("-" * 30)
        for i, record in enumerate(sm_data, 1):
            month = record.get('month', 'Unknown')
            sm_value = record.get('sm_value', 0)
            print(f"  {i}. {month}: ${sm_value:,.2f}")
        
        sm_values = [r.get('sm_value', 0) for r in sm_data]
        total_sm = sum(sm_values)
        avg_sm = total_sm / len(sm_values) if sm_values else 0
        print(f"\n💰 S&M Statistics:")
        print(f"  Total S&M Spend: ${total_sm:,.2f}")
        print(f"  Average S&M: ${avg_sm:,.2f}")
        
    except Exception as e:
        print(f"❌ Error loading S&M data: {e}")
    
    print()
    
    # Load cohort data
    try:
        with open(cohort_file, 'r') as f:
            cohort_data = json.load(f)
        print(f"📊 REVENUE COHORTS DATA ({len(cohort_data)} records):")
        print("-" * 40)
        for i, record in enumerate(cohort_data, 1):
            cohort_name = record.get('cohort_name', 'Unknown')
            revenue = record.get('first_month_revenue', 0)
            month = record.get('month', 'N/A')
            print(f"  {i}. {cohort_name}: ${revenue:,.2f} (Month: {month})")
        
        revenue_values = [r.get('first_month_revenue', 0) for r in cohort_data]
        total_revenue = sum(revenue_values)
        avg_revenue = total_revenue / len(revenue_values) if revenue_values else 0
        print(f"\n💰 Revenue Statistics:")
        print(f"  Total First Month Revenue: ${total_revenue:,.2f}")
        print(f"  Average First Month Revenue: ${avg_revenue:,.2f}")
        
    except Exception as e:
        print(f"❌ Error loading cohort data: {e}")
    
    print()
    print("📅 Data viewed successfully!")

if __name__ == "__main__":
    load_and_print_data()
