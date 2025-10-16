#!/usr/bin/env python3
"""
Compare All V2V Approaches
Runs all 5 approaches and generates comprehensive comparison report
"""

import pandas as pd
import json
import os
import time
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

def load_approach_results(approach_name, csv_file, json_file):
    """Load results from a specific approach"""
    try:
        if os.path.exists(csv_file) and os.path.exists(json_file):
            csv_data = pd.read_csv(csv_file)
            with open(json_file, 'r') as f:
                json_data = json.load(f)
            
            return {
                'name': approach_name,
                'csv_data': csv_data,
                'json_data': json_data,
                'status': 'success'
            }
        else:
            return {
                'name': approach_name,
                'status': 'missing_files',
                'csv_exists': os.path.exists(csv_file),
                'json_exists': os.path.exists(json_file)
            }
    except Exception as e:
        return {
            'name': approach_name,
            'status': 'error',
            'error': str(e)
        }

def generate_comparison_report(approaches):
    """Generate comprehensive comparison report"""
    print("="*80)
    print("V2V APPROACH COMPARISON REPORT")
    print("="*80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Filter successful approaches
    successful_approaches = [app for app in approaches if app['status'] == 'success']
    
    if not successful_approaches:
        print("❌ No successful approaches found!")
        return None
    
    print(f"📊 Analyzing {len(successful_approaches)} successful approaches:")
    for app in successful_approaches:
        print(f"   ✅ {app['name']}")
    
    print()
    
    # Create comparison table
    comparison_data = []
    
    for app in successful_approaches:
        json_data = app['json_data']
        csv_data = app['csv_data']
        
        # Extract key metrics
        distance_acc = json_data.get('distance_accuracy', {})
        speed_acc_src = json_data.get('speed_accuracy', {}).get('source_vehicle', {})
        speed_acc_dst = json_data.get('speed_accuracy', {}).get('destination_vehicle', {})
        waypoint_dist = json_data.get('waypoint_distribution', {})
        
        comparison_data.append({
            'Approach': app['name'],
            'Mean_Accuracy_%': distance_acc.get('mean_accuracy_pct', 0),
            'Median_Accuracy_%': distance_acc.get('median_accuracy_pct', 0),
            'RMSE_m': distance_acc.get('rmse_m', 0),
            'MAE_m': distance_acc.get('mean_absolute_error_m', 0),
            'High_Acc_90plus': waypoint_dist.get('high_accuracy_90_plus', 0),
            'Medium_Acc_70_89': waypoint_dist.get('medium_accuracy_70_89', 0),
            'Low_Acc_below_70': waypoint_dist.get('low_accuracy_below_70', 0),
            'Total_Waypoints': waypoint_dist.get('total_waypoints_analyzed', 0),
            'Speed_MAE_Src_kmh': speed_acc_src.get('mean_absolute_error_kmh', 0),
            'Speed_MAE_Dst_kmh': speed_acc_dst.get('mean_absolute_error_kmh', 0),
            'Best_Waypoint': json_data.get('best_waypoint', {}).get('waypoint', 0),
            'Best_Accuracy_%': json_data.get('best_waypoint', {}).get('accuracy_pct', 0),
            'Worst_Waypoint': json_data.get('worst_waypoint', {}).get('waypoint', 0),
            'Worst_Accuracy_%': json_data.get('worst_waypoint', {}).get('accuracy_pct', 0)
        })
    
    # Create DataFrame
    comparison_df = pd.DataFrame(comparison_data)
    
    # Sort by mean accuracy (descending)
    comparison_df = comparison_df.sort_values('Mean_Accuracy_%', ascending=False)
    
    print("📊 COMPARISON TABLE:")
    print("-" * 120)
    print(f"{'Approach':<25} {'Mean Acc':<10} {'Median Acc':<12} {'RMSE':<8} {'MAE':<8} {'High Acc':<10} {'Med Acc':<10} {'Low Acc':<10} {'Total WP':<10}")
    print("-" * 120)
    
    for _, row in comparison_df.iterrows():
        print(f"{row['Approach']:<25} {row['Mean_Accuracy_%']:<10.2f} {row['Median_Accuracy_%']:<12.2f} "
              f"{row['RMSE_m']:<8.2f} {row['MAE_m']:<8.2f} {row['High_Acc_90plus']:<10} "
              f"{row['Medium_Acc_70_89']:<10} {row['Low_Acc_below_70']:<10} {row['Total_Waypoints']:<10}")
    
    print("-" * 120)
    print()
    
    # Find best approach
    best_approach = comparison_df.iloc[0]
    print("🏆 WINNER:")
    print(f"   {best_approach['Approach']}")
    print(f"   Mean Accuracy: {best_approach['Mean_Accuracy_%']:.2f}%")
    print(f"   RMSE: {best_approach['RMSE_m']:.2f} m")
    print(f"   High Accuracy Waypoints: {best_approach['High_Acc_90plus']}")
    print()
    
    # Detailed analysis
    print("📊 DETAILED ANALYSIS:")
    print()
    
    for _, row in comparison_df.iterrows():
        print(f"🔍 {row['Approach']}:")
        print(f"   Distance Accuracy: {row['Mean_Accuracy_%']:.2f}% (median: {row['Median_Accuracy_%']:.2f}%)")
        print(f"   Error Metrics: RMSE={row['RMSE_m']:.2f}m, MAE={row['MAE_m']:.2f}m")
        print(f"   Waypoint Distribution: High={row['High_Acc_90plus']}, Medium={row['Medium_Acc_70_89']}, Low={row['Low_Acc_below_70']}")
        print(f"   Speed Accuracy: Source MAE={row['Speed_MAE_Src_kmh']:.2f}km/h, Dest MAE={row['Speed_MAE_Dst_kmh']:.2f}km/h")
        print(f"   Best Waypoint: #{row['Best_Waypoint']} ({row['Best_Accuracy_%']:.2f}%)")
        print(f"   Worst Waypoint: #{row['Worst_Waypoint']} ({row['Worst_Accuracy_%']:.2f}%)")
        print()
    
    # Assessment
    print("📊 OVERALL ASSESSMENT:")
    print()
    
    mean_accuracies = comparison_df['Mean_Accuracy_%'].values
    max_acc = max(mean_accuracies)
    min_acc = min(mean_accuracies)
    avg_acc = np.mean(mean_accuracies)
    
    print(f"   Range: {min_acc:.2f}% - {max_acc:.2f}%")
    print(f"   Average: {avg_acc:.2f}%")
    print(f"   Improvement over baseline: {max_acc - min_acc:.2f} percentage points")
    
    if max_acc >= 80:
        print("   🎯 TARGET ACHIEVED: At least one approach reached 80%+ accuracy!")
    else:
        print(f"   ⚠️ TARGET MISSED: Best approach is {max_acc:.2f}%, need {80 - max_acc:.2f}% more")
    
    print()
    
    return comparison_df

def create_comparison_plots(approaches, comparison_df):
    """Create comparison plots"""
    print("📊 Creating comparison plots...")
    
    successful_approaches = [app for app in approaches if app['status'] == 'success']
    
    if len(successful_approaches) < 2:
        print("⚠️ Need at least 2 approaches for comparison plots")
        return
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('V2V Approach Comparison', fontsize=16, fontweight='bold')
    
    # Plot 1: Mean Accuracy Comparison
    ax1 = axes[0, 0]
    approaches_names = comparison_df['Approach'].values
    mean_accuracies = comparison_df['Mean_Accuracy_%'].values
    
    bars1 = ax1.bar(range(len(approaches_names)), mean_accuracies, 
                    color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'][:len(approaches_names)])
    ax1.set_title('Mean Distance Accuracy (%)')
    ax1.set_ylabel('Accuracy (%)')
    ax1.set_xticks(range(len(approaches_names)))
    ax1.set_xticklabels(approaches_names, rotation=45, ha='right')
    ax1.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for i, bar in enumerate(bars1):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{height:.1f}%', ha='center', va='bottom')
    
    # Plot 2: Error Metrics Comparison
    ax2 = axes[0, 1]
    rmse_values = comparison_df['RMSE_m'].values
    mae_values = comparison_df['MAE_m'].values
    
    x = np.arange(len(approaches_names))
    width = 0.35
    
    bars2a = ax2.bar(x - width/2, rmse_values, width, label='RMSE', color='#ff7f0e')
    bars2b = ax2.bar(x + width/2, mae_values, width, label='MAE', color='#2ca02c')
    
    ax2.set_title('Error Metrics (m)')
    ax2.set_ylabel('Error (m)')
    ax2.set_xticks(x)
    ax2.set_xticklabels(approaches_names, rotation=45, ha='right')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Waypoint Distribution
    ax3 = axes[1, 0]
    high_acc = comparison_df['High_Acc_90plus'].values
    med_acc = comparison_df['Medium_Acc_70_89'].values
    low_acc = comparison_df['Low_Acc_below_70'].values
    
    x = np.arange(len(approaches_names))
    width = 0.25
    
    bars3a = ax3.bar(x - width, high_acc, width, label='High (≥90%)', color='#2ca02c')
    bars3b = ax3.bar(x, med_acc, width, label='Medium (70-89%)', color='#ff7f0e')
    bars3c = ax3.bar(x + width, low_acc, width, label='Low (<70%)', color='#d62728')
    
    ax3.set_title('Waypoint Accuracy Distribution')
    ax3.set_ylabel('Number of Waypoints')
    ax3.set_xticks(x)
    ax3.set_xticklabels(approaches_names, rotation=45, ha='right')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Speed Accuracy
    ax4 = axes[1, 1]
    speed_src = comparison_df['Speed_MAE_Src_kmh'].values
    speed_dst = comparison_df['Speed_MAE_Dst_kmh'].values
    
    x = np.arange(len(approaches_names))
    width = 0.35
    
    bars4a = ax4.bar(x - width/2, speed_src, width, label='Source Vehicle', color='#1f77b4')
    bars4b = ax4.bar(x + width/2, speed_dst, width, label='Destination Vehicle', color='#ff7f0e')
    
    ax4.set_title('Speed Accuracy (MAE km/h)')
    ax4.set_ylabel('MAE (km/h)')
    ax4.set_xticks(x)
    ax4.set_xticklabels(approaches_names, rotation=45, ha='right')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save plot
    plot_file = 'comparison_plots.png'
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    print(f"✅ Comparison plots saved to: {plot_file}")
    
    plt.show()

def main():
    """Main comparison function"""
    print("🚀 Starting V2V Approach Comparison")
    print("="*50)
    
    # Define approach files
    approaches = [
        {
            'name': '1. Baseline 200pts',
            'csv_file': 'realistic_speed_waypoint_analysis.csv',
            'json_file': 'realistic_speed_simulation_summary.json'
        },
        {
            'name': '2. Improved Routing',
            'csv_file': 'approach_2_improved_routing_analysis.csv',
            'json_file': 'approach_2_improved_routing_summary.json'
        },
        {
            'name': '3. GPS Forcing',
            'csv_file': 'approach_3_gps_forcing_analysis.csv',
            'json_file': 'approach_3_gps_forcing_summary.json'
        },
        {
            'name': '4. Hybrid',
            'csv_file': 'approach_4_hybrid_analysis.csv',
            'json_file': 'approach_4_hybrid_summary.json'
        },
        {
            'name': '5. Fine-Tuned Calib',
            'csv_file': 'approach_5_fine_tuned_calib_analysis.csv',
            'json_file': 'approach_5_fine_tuned_calib_summary.json'
        }
    ]
    
    # Load all approach results
    print("📂 Loading approach results...")
    loaded_approaches = []
    
    for approach in approaches:
        print(f"   Loading {approach['name']}...")
        result = load_approach_results(approach['name'], approach['csv_file'], approach['json_file'])
        loaded_approaches.append(result)
        
        if result['status'] == 'success':
            print(f"   ✅ {approach['name']} loaded successfully")
        elif result['status'] == 'missing_files':
            print(f"   ⚠️ {approach['name']} - missing files")
        else:
            print(f"   ❌ {approach['name']} - error: {result.get('error', 'Unknown')}")
    
    print()
    
    # Generate comparison report
    comparison_df = generate_comparison_report(loaded_approaches)
    
    if comparison_df is not None:
        # Save comparison CSV
        comparison_csv = 'comparison_report.csv'
        comparison_df.to_csv(comparison_csv, index=False)
        print(f"💾 Comparison CSV saved to: {comparison_csv}")
        
        # Create plots
        try:
            create_comparison_plots(loaded_approaches, comparison_df)
        except Exception as e:
            print(f"⚠️ Error creating plots: {e}")
        
        # Generate recommendations
        print("\n📊 RECOMMENDATIONS:")
        print("="*50)
        
        best_approach = comparison_df.iloc[0]
        best_name = best_approach['Approach']
        best_acc = best_approach['Mean_Accuracy_%']
        
        print(f"1. 🏆 BEST APPROACH: {best_name}")
        print(f"   - Achieves {best_acc:.2f}% mean accuracy")
        print(f"   - RMSE: {best_approach['RMSE_m']:.2f}m")
        print(f"   - High accuracy waypoints: {best_approach['High_Acc_90plus']}")
        
        if best_acc >= 80:
            print("   ✅ TARGET ACHIEVED: 80%+ accuracy reached!")
        else:
            print(f"   ⚠️ TARGET MISSED: Need {80 - best_acc:.2f}% more accuracy")
        
        print()
        
        # Analyze improvements
        if len(comparison_df) > 1:
            baseline_acc = comparison_df[comparison_df['Approach'] == '1. Baseline 200pts']['Mean_Accuracy_%'].iloc[0] if '1. Baseline 200pts' in comparison_df['Approach'].values else None
            
            if baseline_acc is not None:
                improvement = best_acc - baseline_acc
                print(f"2. 📈 IMPROVEMENT ANALYSIS:")
                print(f"   - Baseline accuracy: {baseline_acc:.2f}%")
                print(f"   - Best approach accuracy: {best_acc:.2f}%")
                print(f"   - Improvement: +{improvement:.2f} percentage points")
                
                if improvement > 0:
                    print(f"   ✅ Positive improvement achieved!")
                else:
                    print(f"   ⚠️ No improvement over baseline")
        
        print()
        print("3. 🔧 IMPLEMENTATION RECOMMENDATION:")
        print(f"   - Integrate {best_name} into main v2v_realistic_speed_simulation.py")
        print(f"   - Use as the default approach for future simulations")
        print(f"   - Consider combining with other successful techniques")
        
        print()
        print("4. 📊 NEXT STEPS:")
        print("   - Run extended tests with full 200 waypoints")
        print("   - Validate results with different vehicle pairs")
        print("   - Optimize parameters further if needed")
        
    else:
        print("❌ No successful approaches found for comparison")
    
    print("\n" + "="*80)
    print("✅ COMPARISON COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
