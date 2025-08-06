import json
import os
import random
from datetime import datetime, timedelta
import calendar
from prediction_engine import (
    normalize_month_name, month_to_datetime, get_next_12_months,
    load_historical_data, calculate_12_month_cac, build_prediction_algorithm,
    calculate_rolling_3m_cac
)

def run_single_prediction(sm_dict, revenue_dict, algorithm_data):
    """Run a single prediction and return the rolling 3M averages"""
    # Get the last month from historical data
    all_months = list(set(sm_dict.keys()) | set(revenue_dict.keys()))
    all_months.sort(key=month_to_datetime)
    last_month = all_months[-1]
    
    # Get next 12 months
    next_12_months = get_next_12_months(last_month)
    
    # Get last S&M value for growth calculation
    last_sm = sm_dict.get(last_month, 0)
    
    predictions = []
    
    for i, month in enumerate(next_12_months):
        # Calculate S&M for this month (10% growth per month)
        sm_value = last_sm * (1.1 ** (i + 1))
        
        # Simulate S&M/Revenue ratio
        # Throw die with heads_percentage probability
        if random.random() < algorithm_data['heads_percentage']:
            # Heads: S&M/Revenue = S&M value
            predicted_ratio = sm_value
        else:
            # Tails: Pick random value from distribution
            if algorithm_data['distribution']:
                predicted_ratio = random.choice(algorithm_data['distribution'])
            else:
                predicted_ratio = algorithm_data['cac_12m']  # fallback
        
        # Calculate predicted revenue
        predicted_revenue = sm_value / predicted_ratio if predicted_ratio > 0 else 0
        
        predictions.append({
            'month': month,
            'sm_value': sm_value,
            'predicted_ratio': predicted_ratio,
            'predicted_revenue': predicted_revenue
        })
    
    # Extract rolling 3M averages (skip first 2 months which are N/A)
    rolling_3m_values = []
    for i in range(2, len(predictions)):  # Start from index 2 (3rd month)
        rolling_3m = calculate_rolling_3m_cac(predictions, i)
        if rolling_3m is not None:
            rolling_3m_values.append(rolling_3m)
    
    return rolling_3m_values

def run_monte_carlo_simulation(num_simulations=1000):
    """Run Monte Carlo simulation for both conservative and less conservative models"""
    print("🎲 MONTE CARLO SIMULATION - Both Models")
    print("=" * 80)
    print(f"Running {num_simulations} simulations for each model...")
    
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
    
    # Run conservative simulations
    print(f"\n🔄 Running conservative simulations...")
    conservative_rolling_3m_values = []
    for i in range(num_simulations):
        if (i + 1) % 100 == 0:
            print(f"  Conservative: Completed {i + 1}/{num_simulations} simulations...")
        
        rolling_3m_values = run_single_prediction(sm_dict, revenue_dict, conservative_algorithm)
        conservative_rolling_3m_values.extend(rolling_3m_values)
    
    # Run less conservative simulations
    print(f"\n🔄 Running less conservative simulations...")
    less_conservative_rolling_3m_values = []
    for i in range(num_simulations):
        if (i + 1) % 100 == 0:
            print(f"  Less Conservative: Completed {i + 1}/{num_simulations} simulations...")
        
        rolling_3m_values = run_single_prediction(sm_dict, revenue_dict, less_conservative_algorithm)
        less_conservative_rolling_3m_values.extend(rolling_3m_values)
    
    print(f"\n✅ Simulation complete!")
    print(f"Conservative rolling 3M average values: {len(conservative_rolling_3m_values)}")
    print(f"Less conservative rolling 3M average values: {len(less_conservative_rolling_3m_values)}")
    print(f"Total values: {len(conservative_rolling_3m_values) + len(less_conservative_rolling_3m_values)}")
    
    # Calculate statistics for conservative model
    if conservative_rolling_3m_values:
        conservative_avg = sum(conservative_rolling_3m_values) / len(conservative_rolling_3m_values)
        conservative_min = min(conservative_rolling_3m_values)
        conservative_max = max(conservative_rolling_3m_values)
        
        print(f"\n📊 CONSERVATIVE MODEL STATISTICS:")
        print(f"  Average rolling 3M CAC: {conservative_avg:.2f}")
        print(f"  Minimum rolling 3M CAC: {conservative_min:.2f}")
        print(f"  Maximum rolling 3M CAC: {conservative_max:.2f}")
        print(f"  Range: {conservative_max - conservative_min:.2f}")
        
        # Calculate percentage thresholds for conservative
        thresholds = [20, 30, 40, 50, 60, 70, 80, 90, 100]
        print(f"\n📈 CONSERVATIVE - PERCENTAGE ABOVE THRESHOLDS:")
        print("-" * 50)
        
        conservative_threshold_percentages = {}
        for threshold in thresholds:
            count_above = sum(1 for value in conservative_rolling_3m_values if value > threshold)
            percentage = (count_above / len(conservative_rolling_3m_values)) * 100
            conservative_threshold_percentages[f"above_{threshold}"] = percentage
            print(f"  Above {threshold:3.0f}: {percentage:6.2f}% ({count_above:5d} values)")
    
    # Calculate statistics for less conservative model
    if less_conservative_rolling_3m_values:
        less_conservative_avg = sum(less_conservative_rolling_3m_values) / len(less_conservative_rolling_3m_values)
        less_conservative_min = min(less_conservative_rolling_3m_values)
        less_conservative_max = max(less_conservative_rolling_3m_values)
        
        print(f"\n📊 LESS CONSERVATIVE MODEL STATISTICS:")
        print(f"  Average rolling 3M CAC: {less_conservative_avg:.2f}")
        print(f"  Minimum rolling 3M CAC: {less_conservative_min:.2f}")
        print(f"  Maximum rolling 3M CAC: {less_conservative_max:.2f}")
        print(f"  Range: {less_conservative_max - less_conservative_min:.2f}")
        
        # Calculate percentage thresholds for less conservative
        print(f"\n📈 LESS CONSERVATIVE - PERCENTAGE ABOVE THRESHOLDS:")
        print("-" * 50)
        
        less_conservative_threshold_percentages = {}
        for threshold in thresholds:
            count_above = sum(1 for value in less_conservative_rolling_3m_values if value > threshold)
            percentage = (count_above / len(less_conservative_rolling_3m_values)) * 100
            less_conservative_threshold_percentages[f"above_{threshold}"] = percentage
            print(f"  Above {threshold:3.0f}: {percentage:6.2f}% ({count_above:5d} values)")
    
    # Save results
    simulation_results = {
        'simulation_parameters': {
            'num_simulations': num_simulations,
            'conservative_algorithm': conservative_algorithm,
            'less_conservative_algorithm': less_conservative_algorithm,
            'simulation_date': datetime.now().isoformat()
        },
        'conservative': {
            'rolling_3m_values': conservative_rolling_3m_values,
            'statistics': {
                'count': len(conservative_rolling_3m_values),
                'average': conservative_avg if conservative_rolling_3m_values else 0,
                'minimum': conservative_min if conservative_rolling_3m_values else 0,
                'maximum': conservative_max if conservative_rolling_3m_values else 0,
                'range': conservative_max - conservative_min if conservative_rolling_3m_values else 0
            },
            'threshold_percentages': conservative_threshold_percentages if conservative_rolling_3m_values else {}
        },
        'less_conservative': {
            'rolling_3m_values': less_conservative_rolling_3m_values,
            'statistics': {
                'count': len(less_conservative_rolling_3m_values),
                'average': less_conservative_avg if less_conservative_rolling_3m_values else 0,
                'minimum': less_conservative_min if less_conservative_rolling_3m_values else 0,
                'maximum': less_conservative_max if less_conservative_rolling_3m_values else 0,
                'range': less_conservative_max - less_conservative_min if less_conservative_rolling_3m_values else 0
            },
            'threshold_percentages': less_conservative_threshold_percentages if less_conservative_rolling_3m_values else {}
        }
    }
    
    with open('monte_carlo_both_models.json', 'w') as f:
        json.dump(simulation_results, f, indent=2)
    
    print(f"\n💾 Results saved to: monte_carlo_both_models.json")
    print("=" * 80)
    
    return conservative_rolling_3m_values, less_conservative_rolling_3m_values

if __name__ == "__main__":
    run_monte_carlo_simulation(10000) 