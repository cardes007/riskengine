import json
from datetime import datetime

def calculate_ndr_evolution():
    with open('full_cohort_data.json', 'r') as f:
        cohorts_data = json.load(f)

    num_months = len(cohorts_data[0]['revenue_array'])
    if num_months < 13:
        print("Not enough months of data to calculate NDR (need at least 13).")
        return

    print("📊 NET DOLLAR RETENTION (NDR) EVOLUTION OVER TIME")
    print("=" * 80)

    ndr_evolution = []
    month_labels = [f"M{i+1}" for i in range(num_months)]

    # For each possible ending month (from last col to col 12)
    for end_col in range(num_months-1, 11, -1):
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
        ndr_evolution.append((month_labels[end_col], ndr))

    # Print the NDR evolution array
    print("NDR Evolution (most recent first):")
    for label, ndr in ndr_evolution:
        if ndr is not None:
            print(f"  {label}: {ndr:.2%}")
        else:
            print(f"  {label}: N/A")
    print("\nNDR values array:")
    ndr_values = [ndr for label, ndr in ndr_evolution if ndr is not None]
    print(ndr_values)

    # Calculate the median NDR and its 12th root
    if ndr_values:
        import statistics
        median_ndr = statistics.median(ndr_values)
        monthly_retention = median_ndr ** (1/12)
        print(f"\nMedian NDR: {median_ndr:.4f} ({median_ndr:.2%})")
        print(f"12th root of median NDR (implied median monthly retention): {monthly_retention:.4f} ({monthly_retention:.2%})")

    print(f"\nData exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    calculate_ndr_evolution() 