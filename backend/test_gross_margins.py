#!/usr/bin/env python3
"""
Test script to demonstrate gross margin calculations using P&L data
"""

import json
from prediction_engine import load_pl_data

def test_gross_margins():
    """Test gross margin calculations"""
    print("🧮 TESTING GROSS MARGIN CALCULATIONS")
    print("=" * 60)
    
    # Load P&L data
    revenue_dict, cogs_dict, gross_margin_dict = load_pl_data()
    
    if not revenue_dict:
        print("❌ No P&L data found. Please import data through the frontend first.")
        return
    
    print(f"📊 Loaded data for {len(revenue_dict)} months")
    print("\n📈 GROSS MARGIN ANALYSIS:")
    print("-" * 60)
    print(f"{'Month':<15} {'Revenue':<12} {'COGS':<12} {'Gross Margin %':<15}")
    print("-" * 60)
    
    total_revenue = 0
    total_cogs = 0
    valid_months = 0
    
    for month in sorted(revenue_dict.keys()):
        revenue = revenue_dict[month]
        cogs = cogs_dict[month]
        gross_margin = gross_margin_dict[month]
        
        if revenue > 0:  # Only show months with revenue
            print(f"{month:<15} ${revenue:>10,.0f} ${cogs:>10,.0f} {gross_margin:>12.1f}%")
            total_revenue += revenue
            total_cogs += cogs
            valid_months += 1
    
    print("-" * 60)
    if valid_months > 0:
        overall_gross_margin = ((total_revenue - total_cogs) / total_revenue) * 100
        print(f"{'TOTAL':<15} ${total_revenue:>10,.0f} ${total_cogs:>10,.0f} {overall_gross_margin:>12.1f}%")
        print(f"\n📊 SUMMARY:")
        print(f"  Total months with revenue: {valid_months}")
        print(f"  Total revenue: ${total_revenue:,.0f}")
        print(f"  Total COGS: ${total_cogs:,.0f}")
        print(f"  Overall gross margin: {overall_gross_margin:.1f}%")
        
        # Calculate average gross margin
        avg_gross_margin = sum(gross_margin_dict.values()) / len(gross_margin_dict)
        print(f"  Average gross margin: {avg_gross_margin:.1f}%")
        
        # Find min and max gross margins
        valid_margins = [gm for gm in gross_margin_dict.values() if gm > 0]
        if valid_margins:
            min_margin = min(valid_margins)
            max_margin = max(valid_margins)
            print(f"  Min gross margin: {min_margin:.1f}%")
            print(f"  Max gross margin: {max_margin:.1f}%")
    else:
        print("❌ No valid revenue data found")
    
    print("=" * 60)

if __name__ == "__main__":
    test_gross_margins() 