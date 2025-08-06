import json
import os
from datetime import datetime

def create_cac_table():
    print("📊 CAC ANALYSIS TABLE")
    print("=" * 80)
    
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
    except Exception as e:
        print(f"❌ Error loading S&M data: {e}")
        return
    
    # Load cohort data
    try:
        with open(cohort_file, 'r') as f:
            cohort_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading cohort data: {e}")
        return
    
    # Create a dictionary to match S&M data with cohort data by month
    sm_dict = {}
    for record in sm_data:
        month = record.get('month', '')
        sm_value = record.get('sm_value', 0)
        sm_dict[month] = sm_value
    
    cohort_dict = {}
    for record in cohort_data:
        month = record.get('month', '')
        revenue = record.get('first_month_revenue', 0)
        cohort_dict[month] = revenue
    
    # Create the CAC analysis table
    print("📈 MONTHLY CAC ANALYSIS TABLE")
    print("=" * 80)
    print(f"{'Month':<20} {'S&M Spend':<15} {'New Revenue':<15} {'CAC Ratio':<15} {'Status':<10}")
    print("-" * 80)
    
    all_months = set(sm_dict.keys()) | set(cohort_dict.keys())
    sorted_months = sorted(all_months)
    
    total_sm = 0
    total_revenue = 0
    cac_ratios = []
    
    for month in sorted_months:
        sm_spend = sm_dict.get(month, 0)
        new_revenue = cohort_dict.get(month, 0)
        
        # Calculate CAC ratio
        if new_revenue > 0:
            cac_ratio = sm_spend / new_revenue
            cac_ratios.append(cac_ratio)
            status = "✅" if cac_ratio < 1.0 else "⚠️" if cac_ratio < 2.0 else "❌"
        else:
            cac_ratio = float('inf') if sm_spend > 0 else 0
            status = "❌" if sm_spend > 0 else "⚪"
        
        # Format month for display
        if month.startswith('2024-'):
            # Convert ISO date to readable format
            try:
                date_obj = datetime.fromisoformat(month.replace('T00:00:00.000', ''))
                display_month = date_obj.strftime('%b %Y')
            except:
                display_month = month
        else:
            display_month = month
        
        print(f"{display_month:<20} ${sm_spend:>12,.0f} ${new_revenue:>12,.0f} {cac_ratio:>12.2f} {status:<10}")
        
        total_sm += sm_spend
        total_revenue += new_revenue
    
    print("-" * 80)
    print(f"{'TOTALS':<20} ${total_sm:>12,.0f} ${total_revenue:>12,.0f}")
    
    # Calculate overall CAC
    if total_revenue > 0:
        overall_cac = total_sm / total_revenue
        print(f"{'OVERALL CAC':<20} {'':<15} {'':<15} {overall_cac:>12.2f}")
    
    print()
    
    # Summary statistics
    if cac_ratios:
        print("📊 CAC STATISTICS:")
        print(f"  Average CAC: {sum(cac_ratios) / len(cac_ratios):.2f}")
        print(f"  Min CAC: {min(cac_ratios):.2f}")
        print(f"  Max CAC: {max(cac_ratios):.2f}")
        
        # Business insights
        print("\n💡 BUSINESS INSIGHTS:")
        profitable_months = [r for r in cac_ratios if r < 1.0]
        reasonable_months = [r for r in cac_ratios if 1.0 <= r < 2.0]
        high_cac_months = [r for r in cac_ratios if r >= 2.0]
        
        print(f"  Profitable months (CAC < 1.0): {len(profitable_months)}")
        print(f"  Reasonable months (CAC 1.0-2.0): {len(reasonable_months)}")
        print(f"  High CAC months (CAC ≥ 2.0): {len(high_cac_months)}")
        
        if overall_cac < 1.0:
            print(f"  🟢 Overall CAC of {overall_cac:.2f} is excellent! You're acquiring customers profitably.")
        elif overall_cac < 2.0:
            print(f"  🟡 Overall CAC of {overall_cac:.2f} is reasonable but could be optimized.")
        else:
            print(f"  🔴 Overall CAC of {overall_cac:.2f} is high. Consider optimizing your marketing spend.")
    
    print()
    print(f"📅 Analysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    create_cac_table() 