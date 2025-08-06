import json
import os
import random
from datetime import datetime, timedelta
import calendar
import math

def normalize_month_name(month_str):
    """Convert month names to a standard format for matching"""
    if len(month_str) <= 7 and ' ' in month_str:
        month_abbr, year = month_str.split(' ')
        month_map = {
            'Jan': 'January', 'Feb': 'February', 'Mar': 'March', 'Apr': 'April',
            'May': 'May', 'Jun': 'June', 'Jul': 'July', 'Aug': 'August',
            'Sep': 'September', 'Oct': 'October', 'Nov': 'November', 'Dec': 'December'
        }
        if month_abbr in month_map:
            return f"{month_map[month_abbr]} 20{year}"
    return month_str

def month_to_datetime(month_str):
    """Convert month string to datetime for chronological sorting"""
    try:
        return datetime.strptime(month_str, "%B %Y")
    except ValueError:
        return datetime(1900, 1, 1)

def get_next_12_months(last_month_str):
    """Generate the next 12 months after the last month in the data"""
    last_date = month_to_datetime(last_month_str)
    next_months = []
    
    for i in range(1, 13):
        # Add months to the last date
        if last_date.month == 12:
            next_date = last_date.replace(year=last_date.year + 1, month=1)
        else:
            next_date = last_date.replace(month=last_date.month + 1)
        
        next_months.append(next_date.strftime("%B %Y"))
        last_date = next_date
    
    return next_months

def load_historical_data():
    """Load and process historical data"""
    # Load S&M data from P&L
    try:
        with open('pl_data.json', 'r') as f:
            pl_data = json.load(f)
    except FileNotFoundError:
        print("Warning: pl_data.json not found. Using empty S&M data.")
        return {}, {}
    
    # Load cohort data for New Revenue (first month revenue)
    try:
        with open('full_cohort_data.json', 'r') as f:
            cohort_data = json.load(f)
    except FileNotFoundError:
        print("Warning: full_cohort_data.json not found. Using empty revenue data.")
        return {}, {}
    
    # Create dictionaries
    sm_dict = {}
    for record in pl_data:
        month = normalize_month_name(record['month'])
        sm_value = record.get('sm', 0)
        try:
            sm_value = float(sm_value) if sm_value != '' else 0
        except (ValueError, TypeError):
            sm_value = 0
        sm_dict[month] = sm_value
    
    # Create New Revenue dictionary from cohort data
    revenue_dict = {}
    for record in cohort_data:
        if record['cohort_name'] == 'Older Cohorts':
            continue
        month = normalize_month_name(record['month'])
        revenue = record['revenue_array'][0] if record['revenue_array'] else 0  # Use first month revenue
        try:
            revenue = float(revenue) if revenue != '' else 0
        except (ValueError, TypeError):
            revenue = 0
        revenue_dict[month] = revenue
    
    return sm_dict, revenue_dict

def load_pl_data():
    """Load P&L data and calculate gross margins"""
    try:
        with open('pl_data.json', 'r') as f:
            pl_data = json.load(f)
    except FileNotFoundError:
        print("Warning: pl_data.json not found. Gross margin calculations will not be available.")
        return {}, {}, {}
    
    # Create dictionaries for revenue, COGS, and gross margins
    revenue_dict = {}
    cogs_dict = {}
    gross_margin_dict = {}
    
    for record in pl_data:
        month = normalize_month_name(record['month'])
        revenue = record.get('revenue', 0)
        cogs = record.get('cogs', 0)
        
        # Convert to float, handle empty strings
        try:
            revenue = float(revenue) if revenue != '' else 0
            cogs = float(cogs) if cogs != '' else 0
        except (ValueError, TypeError):
            revenue = 0
            cogs = 0
        
        revenue_dict[month] = revenue
        cogs_dict[month] = cogs
        
        # Calculate gross margin percentage
        if revenue > 0:
            gross_margin_pct = ((revenue - cogs) / revenue) * 100
        else:
            gross_margin_pct = 0
        
        gross_margin_dict[month] = gross_margin_pct
    
    return revenue_dict, cogs_dict, gross_margin_dict

def calculate_12_month_cac(sm_dict, revenue_dict):
    """Calculate 12-month CAC ratio and marginal 12-month CAC if possible. Return the max of both."""
    all_months = list(set(sm_dict.keys()) | set(revenue_dict.keys()))
    all_months.sort(key=month_to_datetime)
    
    last_12_months = all_months[-12:] if len(all_months) >= 12 else all_months
    total_sm_12m = sum((sm_dict.get(month, 0) or 0) for month in last_12_months)
    total_revenue_12m = sum((revenue_dict.get(month, 0) or 0) for month in last_12_months)
    cac_12m = total_sm_12m / total_revenue_12m if total_revenue_12m > 0 else 0

    # Marginal CAC: requires at least 24 months
    marginal_cac = None
    if len(all_months) >= 24:
        prev_12_months = all_months[-24:-12]
        sm_last_12 = sum((sm_dict.get(month, 0) or 0) for month in last_12_months)
        sm_prev_12 = sum((sm_dict.get(month, 0) or 0) for month in prev_12_months)
        rev_last_12 = sum((revenue_dict.get(month, 0) or 0) for month in last_12_months)
        rev_prev_12 = sum((revenue_dict.get(month, 0) or 0) for month in prev_12_months)
        sm_diff = sm_last_12 - sm_prev_12
        rev_diff = rev_last_12 - rev_prev_12
        if rev_diff > 0:
            marginal_cac = sm_diff / rev_diff
        else:
            marginal_cac = 0
    # Return the maximum of the two (if marginal_cac is available)
    if marginal_cac is not None:
        return max(cac_12m, marginal_cac)
    else:
        return cac_12m

def build_prediction_algorithm(sm_dict, revenue_dict, conservative):
    """Build the prediction algorithm based on historical data"""
    # Get all months and sort chronologically
    all_months = list(set(sm_dict.keys()) | set(revenue_dict.keys()))
    all_months.sort(key=month_to_datetime)
    
    # Calculate S&M/Revenue ratios for each month
    ratios = []
    monthly_ratios = {}  # Store ratios by month for last 12 months calculation
    
    for month in all_months:
        sm = sm_dict.get(month, 0)
        revenue = revenue_dict.get(month, 0)
        if revenue is not None and revenue > 0:
            ratio = sm / revenue
            ratios.append(ratio)
            monthly_ratios[month] = ratio
        else:
            # Include None for months with no revenue or zero revenue
            ratios.append(None)
            monthly_ratios[month] = None
    # Step 1: Calculate heads_percentage (% of times ratio > 10000 or is null/non-finite)
    heads_count = sum(
        1 for ratio in ratios
        if ratio is None or not isinstance(ratio, (int, float)) or not math.isfinite(ratio) or ratio > 10000
    )
    heads_percentage_overall = heads_count / len(ratios) if ratios else 0
    
    # Calculate heads percentage for last 12 months
    last_12_months = all_months[-12:] if len(all_months) >= 12 else all_months
    last_12_ratios = [monthly_ratios[month] for month in last_12_months if month in monthly_ratios]
    heads_count_last_12 = sum(
        1 for ratio in last_12_ratios
        if ratio is None or not isinstance(ratio, (int, float)) or not math.isfinite(ratio) or ratio > 10000
    )
    heads_percentage_last_12 = heads_count_last_12 / len(last_12_ratios) if last_12_ratios else 0
    
    # For conservative algorithm, take maximum
    if conservative:
        # Take the maximum of overall and last 12 months
        heads_percentage = max(heads_percentage_overall, heads_percentage_last_12)
        
        heads_percentage_pct = heads_percentage * 100
    else:
        # Less conservative: use overall percentage as is
        heads_percentage = heads_percentage_overall
    
    # Step 2: Build distribution (ratios < 10000, adjusted for 12-month CAC)
    cac_12m = calculate_12_month_cac(sm_dict, revenue_dict)
    distribution = []
    
    for ratio in ratios:
        if ratio is not None and ratio < 10000:
            distribution.append(ratio)
    
    return {
        'heads_percentage': heads_percentage,
        'heads_percentage_overall': heads_percentage_overall,
        'heads_percentage_last_12': heads_percentage_last_12,
        'distribution': distribution,
        'cac_12m': cac_12m,
        'historical_ratios': ratios,
        'conservative': conservative
    }

def predict_next_12_months(sm_dict, revenue_dict, algorithm_data):
    """Predict S&M/Revenue for next 12 months"""
    # Get the last month that has S&M data (not just any data)
    sm_months = list(sm_dict.keys())
    sm_months.sort(key=month_to_datetime)
    if not sm_months:
        return []
    last_month = sm_months[-1]
    
    # Get next 12 months
    next_12_months = get_next_12_months(last_month)
    
    # Get last S&M value for growth calculation
    last_sm = sm_dict.get(last_month, 0)
    

    
    predictions = []
    
    for i, month in enumerate(next_12_months):
        # Calculate S&M for this month (10% growth per month)
        sm_value = last_sm * (1.1 ** (i + 1))
        original_drawn_ratio = None
        # Simulate S&M/Revenue ratio
        # Throw die with heads_percentage probability
        if random.random() < algorithm_data['heads_percentage']:
            # Heads: S&M/Revenue = S&M value
            predicted_ratio = sm_value
            original_drawn_ratio = sm_value
        else:
            # Tails: Pick random value from distribution
            if algorithm_data['distribution']:
                drawn_ratio = random.choice(algorithm_data['distribution'])
                original_drawn_ratio = drawn_ratio
                # Conservative: If drawn_ratio < cac_12m, blend as described
                if algorithm_data.get('conservative', False) and drawn_ratio < algorithm_data['cac_12m']:
                    # Blended ratio: last_sm uses drawn_ratio, extra uses cac_12m
                    if sm_value > last_sm and drawn_ratio > 0:
                        blended_ratio = (
                            sm_value / ((last_sm / drawn_ratio)+((sm_value - last_sm) / algorithm_data['cac_12m']))
                        )
                    else:
                        blended_ratio = drawn_ratio  # If no extra S&M or drawn_ratio is 0, just use drawn_ratio
                    predicted_ratio = blended_ratio
                else:
                    predicted_ratio = drawn_ratio
            else:
                predicted_ratio = algorithm_data['cac_12m']  # fallback
                original_drawn_ratio = algorithm_data['cac_12m']
        
        # Calculate predicted revenue
        predicted_revenue = sm_value / predicted_ratio if predicted_ratio > 0 else 0
        
        predictions.append({
            'month': month,
            'sm_value': sm_value,
            'predicted_ratio': predicted_ratio,
            'predicted_revenue': predicted_revenue,
            'original_drawn_ratio': original_drawn_ratio
        })
    
    return predictions

def calculate_rolling_3m_cac(predictions, month_index):
    """Calculate rolling 3-month CAC for predicted data"""
    if month_index < 2:  # Not enough data for first 2 months
        return None
    
    # Get current month and previous 2 months
    current_month = predictions[month_index]
    prev_month_1 = predictions[month_index - 1]
    prev_month_2 = predictions[month_index - 2]
    
    # Calculate totals for rolling 3 months
    total_sm_3m = (current_month['sm_value'] + 
                   prev_month_1['sm_value'] + 
                   prev_month_2['sm_value'])
    
    total_revenue_3m = (current_month['predicted_revenue'] + 
                       prev_month_1['predicted_revenue'] + 
                       prev_month_2['predicted_revenue'])
    
    # Calculate rolling 3-month CAC
    if total_revenue_3m > 0:
        return total_sm_3m / total_revenue_3m
    else:
        return 0

def run_both_predictions():
    """Run both conservative and less conservative predictions"""
    print("🔮 PREDICTION ENGINE - Both Conservative and Less Conservative")
    print("=" * 100)
    
    # Load historical data
    sm_dict, revenue_dict = load_historical_data()
    
    # Build both prediction algorithms
    print("📊 Building prediction algorithms from historical data...")
    conservative_algorithm = build_prediction_algorithm(sm_dict, revenue_dict, conservative=True)
    less_conservative_algorithm = build_prediction_algorithm(sm_dict, revenue_dict, conservative=False)
    
    print(f"Conservative Algorithm Parameters:")
    print(f"  Heads percentage: {conservative_algorithm['heads_percentage']:.2%}")
    print(f"  12-Month CAC: {conservative_algorithm['cac_12m']:.2f}")
    print(f"  Distribution size: {len(conservative_algorithm['distribution'])} values")
    print(f"  Conservative: {conservative_algorithm['conservative']}")
    
    print(f"\nLess Conservative Algorithm Parameters:")
    print(f"  Heads percentage: {less_conservative_algorithm['heads_percentage']:.2%}")
    print(f"  12-Month CAC: {less_conservative_algorithm['cac_12m']:.2f}")
    print(f"  Distribution size: {len(less_conservative_algorithm['distribution'])} values")
    print(f"  Conservative: {less_conservative_algorithm['conservative']}")
    
    # Run both predictions
    print(f"\n🎲 Running simulations...")
    conservative_predictions = predict_next_12_months(sm_dict, revenue_dict, conservative_algorithm)
    less_conservative_predictions = predict_next_12_months(sm_dict, revenue_dict, less_conservative_algorithm)
    
    # Display conservative results
    print(f"\n📈 CONSERVATIVE PREDICTIONS")
    print("=" * 100)
    print(f"{'Month':<20} {'S&M':<15} {'Predicted Ratio':<15} {'Original Drawn':<15} {'Predicted Revenue':<15} {'Rolling 3M Avg':<15}")
    print("-" * 115)
    
    total_conservative_sm = 0
    total_conservative_revenue = 0
    
    for i, pred in enumerate(conservative_predictions):
        rolling_3m = calculate_rolling_3m_cac(conservative_predictions, i)
        rolling_3m_str = f"{rolling_3m:.2f}" if rolling_3m is not None else "N/A"
        print(f"{pred['month']:<20} ${pred['sm_value']:>12,.0f} {pred['predicted_ratio']:>12.2f} {pred['original_drawn_ratio']:>12.2f} ${pred['predicted_revenue']:>12,.0f} {rolling_3m_str:>15}")
        total_conservative_sm += pred['sm_value']
        total_conservative_revenue += pred['predicted_revenue']
    
    conservative_cac = total_conservative_sm / total_conservative_revenue if total_conservative_revenue > 0 else 0
    print("-" * 100)
    print(f"{'TOTALS':<20} ${total_conservative_sm:>12,.0f} {'':<15} ${total_conservative_revenue:>12,.0f}")
    print(f"{'CONSERVATIVE CAC':<20} {'':<15} {conservative_cac:>12.2f}")
    
    # Display less conservative results
    print(f"\n📈 LESS CONSERVATIVE PREDICTIONS")
    print("=" * 100)
    print(f"{'Month':<20} {'S&M':<15} {'Predicted Ratio':<15} {'Predicted Revenue':<15} {'Rolling 3M Avg':<15}")
    print("-" * 100)
    
    total_less_conservative_sm = 0
    total_less_conservative_revenue = 0
    
    for i, pred in enumerate(less_conservative_predictions):
        rolling_3m = calculate_rolling_3m_cac(less_conservative_predictions, i)
        rolling_3m_str = f"{rolling_3m:.2f}" if rolling_3m is not None else "N/A"
        
        print(f"{pred['month']:<20} ${pred['sm_value']:>12,.0f} {pred['predicted_ratio']:>12.2f} ${pred['predicted_revenue']:>12,.0f} {rolling_3m_str:>15}")
        total_less_conservative_sm += pred['sm_value']
        total_less_conservative_revenue += pred['predicted_revenue']
    
    less_conservative_cac = total_less_conservative_sm / total_less_conservative_revenue if total_less_conservative_revenue > 0 else 0
    print("-" * 100)
    print(f"{'TOTALS':<20} ${total_less_conservative_sm:>12,.0f} {'':<15} ${total_less_conservative_revenue:>12,.0f}")
    print(f"{'LESS CONSERVATIVE CAC':<20} {'':<15} {less_conservative_cac:>12.2f}")
    
    # Save both predictions
    prediction_data = {
        'conservative': {
            'algorithm_parameters': conservative_algorithm,
            'predictions': conservative_predictions,
            'summary': {
                'total_predicted_sm': total_conservative_sm,
                'total_predicted_revenue': total_conservative_revenue,
                'predicted_cac': conservative_cac
            }
        },
        'less_conservative': {
            'algorithm_parameters': less_conservative_algorithm,
            'predictions': less_conservative_predictions,
            'summary': {
                'total_predicted_sm': total_less_conservative_sm,
                'total_predicted_revenue': total_less_conservative_revenue,
                'predicted_cac': less_conservative_cac
            }
        },
        'prediction_date': datetime.now().isoformat()
    }
    
    with open('predictions_both_models.json', 'w') as f:
        json.dump(prediction_data, f, indent=2)
    
    print(f"\n💾 Both predictions saved to: predictions_both_models.json")
    print("=" * 100)
    
    return conservative_algorithm, less_conservative_algorithm

if __name__ == "__main__":
    run_both_predictions() 