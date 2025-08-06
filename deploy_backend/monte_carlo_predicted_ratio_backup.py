import json
import os
import random
from datetime import datetime, timedelta
import calendar
from prediction_engine import (
    normalize_month_name, month_to_datetime, get_next_12_months,
    load_historical_data, calculate_12_month_cac, build_prediction_algorithm
)

def run_single_prediction_ratio(sm_dict, revenue_dict, algorithm_data):
    """Run a single prediction and return the predicted ratios and S&M values as paired data"""
    all_months = list(set(sm_dict.keys()) | set(revenue_dict.keys()))
    all_months.sort(key=month_to_datetime)
    last_month = all_months[-1]

    next_12_months = get_next_12_months(last_month)
    last_sm = sm_dict.get(last_month, 0)

    simulation_data = []

    for i, month in enumerate(next_12_months):
        sm_value = last_sm * (1.1 ** (i + 1))
        
        if random.random() < algorithm_data['heads_percentage']:
            predicted_ratio = sm_value
        else:
            if algorithm_data['distribution']:
                predicted_ratio = random.choice(algorithm_data['distribution'])
            else:
                predicted_ratio = algorithm_data['cac_12m']
        
        # Store as paired data (S&M value and predicted ratio only)
        simulation_data.append({
            'sm_value': sm_value,
            'predicted_ratio': predicted_ratio
        })

    return simulation_data

def run_monte_carlo_predicted_ratio(num_simulations=1000, model_type="both"):
    """Run Monte Carlo simulation for predicted ratios from conservative and/or less conservative models
    
    Args:
        num_simulations (int): Number of simulations to run per model
        model_type (str): Which model(s) to run. Options: 'conservative', 'less_conservative', 'both'
    """
    print("🎲 MONTE CARLO SIMULATION - Predicted Ratios and S&M Values")
    print("=" * 80)
    print(f"Running {num_simulations} simulations for {model_type} model(s)...")
    print(f"Each simulation generates 12 paired values (S&M + Predicted Ratio)")
    
    if model_type == "both":
        print(f"Total paired values per model: {num_simulations * 12:,}")
        print(f"Total paired values for both models: {num_simulations * 12 * 2:,}")
    else:
        print(f"Total paired values: {num_simulations * 12:,}")

    sm_dict, revenue_dict = load_historical_data()

    print("📊 Building prediction algorithms from historical data...")
    
    conservative_simulations = []
    less_conservative_simulations = []
    
    # Build and run conservative model if requested
    if model_type in ['conservative', 'both']:
        conservative_algorithm = build_prediction_algorithm(sm_dict, revenue_dict, conservative=True)
        print(f"Conservative Algorithm Parameters:")
        print(f"  Heads percentage: {conservative_algorithm['heads_percentage']:.2%}")
        print(f"  12-Month CAC: {conservative_algorithm['cac_12m']:.2f}")
        print(f"  Distribution size: {len(conservative_algorithm['distribution'])} values")
        print(f"  Conservative: {conservative_algorithm['conservative']}")
        
        print(f"\n🔄 Running conservative simulations...")
        for i in range(num_simulations):
            if (i + 1) % 100 == 0:
                print(f"  Conservative: Completed {i + 1:,}/{num_simulations:,} simulations...")
            simulation_data = run_single_prediction_ratio(sm_dict, revenue_dict, conservative_algorithm)
            conservative_simulations.extend(simulation_data)

    # Build and run less conservative model if requested
    if model_type in ['less_conservative', 'both']:
        less_conservative_algorithm = build_prediction_algorithm(sm_dict, revenue_dict, conservative=False)
        print(f"\nLess Conservative Algorithm Parameters:")
        print(f"  Heads percentage: {less_conservative_algorithm['heads_percentage']:.2%}")
        print(f"  12-Month CAC: {less_conservative_algorithm['cac_12m']:.2f}")
        print(f"  Distribution size: {len(less_conservative_algorithm['distribution'])} values")
        print(f"  Conservative: {less_conservative_algorithm['conservative']}")
        
        print(f"\n🔄 Running less conservative simulations...")
        for i in range(num_simulations):
            if (i + 1) % 100 == 0:
                print(f"  Less Conservative: Completed {i + 1:,}/{num_simulations:,} simulations...")
            simulation_data = run_single_prediction_ratio(sm_dict, revenue_dict, less_conservative_algorithm)
            less_conservative_simulations.extend(simulation_data)

    print(f"\n✅ Simulation complete!")
    if model_type in ['conservative', 'both']:
        print(f"Conservative simulations: {len(conservative_simulations):,} paired values")
    if model_type in ['less_conservative', 'both']:
        print(f"Less conservative simulations: {len(less_conservative_simulations):,} paired values")
    print(f"Total paired values: {len(conservative_simulations) + len(less_conservative_simulations):,}")

    # Extract separate lists for backward compatibility and statistics
    conservative_predicted_ratios = [item['predicted_ratio'] for item in conservative_simulations]
    conservative_sm_values = [item['sm_value'] for item in conservative_simulations]
    less_conservative_predicted_ratios = [item['predicted_ratio'] for item in less_conservative_simulations]
    less_conservative_sm_values = [item['sm_value'] for item in less_conservative_simulations]

    # Calculate statistics for conservative model
    if conservative_predicted_ratios:
        conservative_avg = sum(conservative_predicted_ratios) / len(conservative_predicted_ratios)
        conservative_min = min(conservative_predicted_ratios)
        conservative_max = max(conservative_predicted_ratios)
        conservative_median = sorted(conservative_predicted_ratios)[len(conservative_predicted_ratios) // 2]

        print(f"\n📊 CONSERVATIVE MODEL - PREDICTED RATIOS STATISTICS:")
        print(f"  Average predicted ratio: {conservative_avg:.2f}")
        print(f"  Median predicted ratio: {conservative_median:.2f}")
        print(f"  Minimum predicted ratio: {conservative_min:.2f}")
        print(f"  Maximum predicted ratio: {conservative_max:.2f}")
        print(f"  Range: {conservative_max - conservative_min:.2f}")

        # Calculate percentiles
        sorted_conservative = sorted(conservative_predicted_ratios)
        p25 = sorted_conservative[int(len(sorted_conservative) * 0.25)]
        p75 = sorted_conservative[int(len(sorted_conservative) * 0.75)]
        p90 = sorted_conservative[int(len(sorted_conservative) * 0.90)]
        p95 = sorted_conservative[int(len(sorted_conservative) * 0.95)]
        p99 = sorted_conservative[int(len(sorted_conservative) * 0.99)]

        print(f"  25th percentile: {p25:.2f}")
        print(f"  75th percentile: {p75:.2f}")
        print(f"  90th percentile: {p90:.2f}")
        print(f"  95th percentile: {p95:.2f}")
        print(f"  99th percentile: {p99:.2f}")

        # Threshold analysis
        thresholds = [20, 30, 40, 50, 60, 70, 80, 90, 100, 200, 500, 1000, 5000, 10000]
        thresholds = [20, 30, 40, 50, 60, 70, 80, 90, 100, 200, 500, 1000, 5000, 10000]
        print(f"\n📈 CONSERVATIVE - PERCENTAGE ABOVE THRESHOLDS:")
        print("-" * 60)

        conservative_threshold_percentages = {}
        for threshold in thresholds:
            count_above = sum(1 for value in conservative_predicted_ratios if value > threshold)
            percentage = (count_above / len(conservative_predicted_ratios)) * 100
            conservative_threshold_percentages[f"above_{threshold}"] = percentage
            print(f"  Above {threshold:5.0f}: {percentage:6.2f}% ({count_above:6d} values)")

    # Calculate statistics for less conservative model
    if less_conservative_predicted_ratios:
        less_conservative_avg = sum(less_conservative_predicted_ratios) / len(less_conservative_predicted_ratios)
        less_conservative_min = min(less_conservative_predicted_ratios)
        less_conservative_max = max(less_conservative_predicted_ratios)
        less_conservative_median = sorted(less_conservative_predicted_ratios)[len(less_conservative_predicted_ratios) // 2]

        print(f"\n📊 LESS CONSERVATIVE MODEL - PREDICTED RATIOS STATISTICS:")
        print(f"  Average predicted ratio: {less_conservative_avg:.2f}")
        print(f"  Median predicted ratio: {less_conservative_median:.2f}")
        print(f"  Minimum predicted ratio: {less_conservative_min:.2f}")
        print(f"  Maximum predicted ratio: {less_conservative_max:.2f}")
        print(f"  Range: {less_conservative_max - less_conservative_min:.2f}")

        # Calculate percentiles
        sorted_less_conservative = sorted(less_conservative_predicted_ratios)
        p25 = sorted_less_conservative[int(len(sorted_less_conservative) * 0.25)]
        p75 = sorted_less_conservative[int(len(sorted_less_conservative) * 0.75)]
        p90 = sorted_less_conservative[int(len(sorted_less_conservative) * 0.90)]
        p95 = sorted_less_conservative[int(len(sorted_less_conservative) * 0.95)]
        p99 = sorted_less_conservative[int(len(sorted_less_conservative) * 0.99)]

        print(f"  25th percentile: {p25:.2f}")
        print(f"  75th percentile: {p75:.2f}")
        print(f"  90th percentile: {p90:.2f}")
        print(f"  95th percentile: {p95:.2f}")
        print(f"  99th percentile: {p99:.2f}")

        # Threshold analysis
        thresholds = [20, 30, 40, 50, 60, 70, 80, 90, 100, 200, 500, 1000, 5000, 10000]
        print(f"\n📈 LESS CONSERVATIVE - PERCENTAGE ABOVE THRESHOLDS:")
        print("-" * 60)

        less_conservative_threshold_percentages = {}
        for threshold in thresholds:
            count_above = sum(1 for value in less_conservative_predicted_ratios if value > threshold)
            percentage = (count_above / len(less_conservative_predicted_ratios)) * 100
            less_conservative_threshold_percentages[f"above_{threshold}"] = percentage
            print(f"  Above {threshold:5.0f}: {percentage:6.2f}% ({count_above:6d} values)")

    # Save results to JSON file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"monte_carlo_predicted_ratios_{model_type}_{timestamp}.json"
    
    results = {
        'metadata': {
            'num_simulations': num_simulations,
            'model_type': model_type,
            'timestamp': timestamp,
            'conservative_algorithm': conservative_algorithm if model_type in ['conservative', 'both'] else None,
            'less_conservative_algorithm': less_conservative_algorithm if model_type in ['less_conservative', 'both'] else None
        },
        'conservative': {
            'simulations': conservative_simulations,
            'predicted_ratios': conservative_predicted_ratios,
            'sm_values': conservative_sm_values,
            'statistics': {
                'average': conservative_avg if conservative_predicted_ratios else None,
                'median': conservative_median if conservative_predicted_ratios else None,
                'minimum': conservative_min if conservative_predicted_ratios else None,
                'maximum': conservative_max if conservative_predicted_ratios else None,
                'range': conservative_max - conservative_min if conservative_predicted_ratios else None,
                'threshold_percentages': conservative_threshold_percentages if conservative_predicted_ratios else {}
            }
        },
        'less_conservative': {
            'simulations': less_conservative_simulations,
            'predicted_ratios': less_conservative_predicted_ratios,
            'sm_values': less_conservative_sm_values,
            'statistics': {
                'average': less_conservative_avg if less_conservative_predicted_ratios else None,
                'median': less_conservative_median if less_conservative_predicted_ratios else None,
                'minimum': less_conservative_min if less_conservative_predicted_ratios else None,
                'maximum': less_conservative_max if less_conservative_predicted_ratios else None,
                'range': less_conservative_max - less_conservative_min if less_conservative_predicted_ratios else None,
                'threshold_percentages': less_conservative_threshold_percentages if less_conservative_predicted_ratios else {}
            }
        }
    }
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {filename}")
    print(f"📊 Data exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    return results

if __name__ == "__main__":
    # Example usage:
    # run_monte_carlo_predicted_ratio(1000, "both")  # Run both models
    # run_monte_carlo_predicted_ratio(1000, "conservative")  # Run only conservative
    # run_monte_carlo_predicted_ratio(1000, "less_conservative")  # Run only less conservative
    run_monte_carlo_predicted_ratio(1000, "both")
