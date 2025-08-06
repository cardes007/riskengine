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
                    if sm_value > last_sm:
                        blended_ratio = (
                            sm_value / ((last_sm / drawn_ratio)+((sm_value - last_sm) / algorithm_data['cac_12m']))
                        )
                    else:
                        blended_ratio = drawn_ratio  # If no extra S&M, just use drawn_ratio
                    predicted_ratio = blended_ratio
                else:
                    predicted_ratio = drawn_ratio
            else:
                predicted_ratio = algorithm_data['cac_12m']  # fallback
                original_drawn_ratio = algorithm_data['cac_12m']
        
        # Store as paired data (S&M value and predicted ratio only)
        simulation_data.append({
            'sm_value': sm_value,
            'predicted_ratio': predicted_ratio
        })

    return simulation_data

def run_monte_carlo_predicted_ratio(num_simulations=1000):
    """Run Monte Carlo simulation for predicted ratios from both conservative and less conservative models"""
    print("🎲 MONTE CARLO SIMULATION - Predicted Ratios and S&M Values")
    print("=" * 80)
    print(f"Running {num_simulations} simulations for each model...")
    print(f"Each simulation generates 12 paired values (S&M + Predicted Ratio)")
    print(f"Total paired values per model: {num_simulations * 12:,}")

    sm_dict, revenue_dict = load_historical_data()

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

    print(f"\n🔄 Running conservative simulations...")
    conservative_simulations = []
    for i in range(num_simulations):
        if (i + 1) % 100 == 0:
            print(f"  Conservative: Completed {i + 1:,}/{num_simulations:,} simulations...")
        simulation_data = run_single_prediction_ratio(sm_dict, revenue_dict, conservative_algorithm)
        conservative_simulations.extend(simulation_data)

    print(f"\n🔄 Running less conservative simulations...")
    less_conservative_simulations = []
    for i in range(num_simulations):
        if (i + 1) % 100 == 0:
            print(f"  Less Conservative: Completed {i + 1:,}/{num_simulations:,} simulations...")
        simulation_data = run_single_prediction_ratio(sm_dict, revenue_dict, less_conservative_algorithm)
        less_conservative_simulations.extend(simulation_data)

    print(f"\n✅ Simulation complete!")
    print(f"Conservative simulations: {len(conservative_simulations):,} paired values")
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

        print(f"\n📈 LESS CONSERVATIVE - PERCENTAGE ABOVE THRESHOLDS:")
        print("-" * 60)

        less_conservative_threshold_percentages = {}
        for threshold in thresholds:
            count_above = sum(1 for value in less_conservative_predicted_ratios if value > threshold)
            percentage = (count_above / len(less_conservative_predicted_ratios)) * 100
            less_conservative_threshold_percentages[f"above_{threshold}"] = percentage
            print(f"  Above {threshold:5.0f}: {percentage:6.2f}% ({count_above:6d} values)")

    # Save results
    simulation_results = {
        'simulation_parameters': {
            'num_simulations': num_simulations,
            'values_per_simulation': 12,
            'total_values_per_model': num_simulations * 12,
            'conservative_algorithm': conservative_algorithm,
            'less_conservative_algorithm': less_conservative_algorithm,
            'simulation_date': datetime.now().isoformat()
        },
        'conservative': {
            'simulations': conservative_simulations,  # Paired data
            'predicted_ratios': conservative_predicted_ratios,  # Backward compatibility
            'sm_values': conservative_sm_values,  # Backward compatibility
            'statistics': {
                'count': len(conservative_predicted_ratios),
                'average': conservative_avg if conservative_predicted_ratios else 0,
                'median': conservative_median if conservative_predicted_ratios else 0,
                'minimum': conservative_min if conservative_predicted_ratios else 0,
                'maximum': conservative_max if conservative_predicted_ratios else 0,
                'range': conservative_max - conservative_min if conservative_predicted_ratios else 0,
                'percentiles': {
                    'p25': p25 if conservative_predicted_ratios else 0,
                    'p75': p75 if conservative_predicted_ratios else 0,
                    'p90': p90 if conservative_predicted_ratios else 0,
                    'p95': p95 if conservative_predicted_ratios else 0,
                    'p99': p99 if conservative_predicted_ratios else 0
                }
            },
            'threshold_percentages': conservative_threshold_percentages if conservative_predicted_ratios else {}
        },
        'less_conservative': {
            'simulations': less_conservative_simulations,  # Paired data
            'predicted_ratios': less_conservative_predicted_ratios,  # Backward compatibility
            'sm_values': less_conservative_sm_values,  # Backward compatibility
            'statistics': {
                'count': len(less_conservative_predicted_ratios),
                'average': less_conservative_avg if less_conservative_predicted_ratios else 0,
                'median': less_conservative_median if less_conservative_predicted_ratios else 0,
                'minimum': less_conservative_min if less_conservative_predicted_ratios else 0,
                'maximum': less_conservative_max if less_conservative_predicted_ratios else 0,
                'range': less_conservative_max - less_conservative_min if less_conservative_predicted_ratios else 0,
                'percentiles': {
                    'p25': p25 if less_conservative_predicted_ratios else 0,
                    'p75': p75 if less_conservative_predicted_ratios else 0,
                    'p90': p90 if less_conservative_predicted_ratios else 0,
                    'p95': p95 if less_conservative_predicted_ratios else 0,
                    'p99': p99 if less_conservative_predicted_ratios else 0
                }
            },
            'threshold_percentages': less_conservative_threshold_percentages if less_conservative_predicted_ratios else {}
        }
    }

    with open('monte_carlo_predicted_ratios.json', 'w') as f:
        json.dump(simulation_results, f, indent=2)

    print(f"\n💾 Monte Carlo predicted ratios and S&M values saved to: monte_carlo_predicted_ratios.json")
    print("=" * 80)

    return simulation_results

if __name__ == "__main__":
    run_monte_carlo_predicted_ratio() 