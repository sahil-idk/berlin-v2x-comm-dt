#!/usr/bin/env python3
"""
Distance Accuracy Analyzer
=========================

This script analyzes the distance accuracy between actual GPS data and simulated vehicle positions.
It provides comprehensive metrics, visualizations, and detailed analysis of how close the 
simulated distances are to the actual distances from the dataset.

Author: AI Assistant
Date: 2024
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def analyze_distance_accuracy(csv_file_path, approach_name="Unknown"):
    """
    Comprehensive distance accuracy analysis
    
    Args:
        csv_file_path: Path to the CSV file with accuracy data
        approach_name: Name of the approach being analyzed
    
    Returns:
        dict: Analysis results
    """
    
    print(f"🔍 Analyzing Distance Accuracy for: {approach_name}")
    print("=" * 60)
    
    # Load data
    try:
        df = pd.read_csv(csv_file_path)
        print(f"✅ Loaded {len(df)} data points from {csv_file_path}")
    except Exception as e:
        print(f"❌ Error loading CSV file: {e}")
        return None
    
    # Check required columns
    required_columns = ['actual_distance', 'simulated_distance', 'accuracy']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"❌ Missing required columns: {missing_columns}")
        return None
    
    # Basic statistics
    print(f"\n📊 BASIC STATISTICS:")
    print(f"   Total waypoints analyzed: {len(df)}")
    print(f"   Actual distance range: {df['actual_distance'].min():.2f}m - {df['actual_distance'].max():.2f}m")
    print(f"   Simulated distance range: {df['simulated_distance'].min():.2f}m - {df['simulated_distance'].max():.2f}m")
    
    # Calculate additional metrics
    if 'calibrated_distance' in df.columns:
        calibrated_distances = df['calibrated_distance']
        print(f"   Calibrated distance range: {calibrated_distances.min():.2f}m - {calibrated_distances.max():.2f}m")
    else:
        calibrated_distances = df['simulated_distance']  # Use simulated if no calibrated column
    
    # Accuracy metrics
    accuracy_stats = {
        'mean_accuracy': df['accuracy'].mean(),
        'median_accuracy': df['accuracy'].median(),
        'std_accuracy': df['accuracy'].std(),
        'min_accuracy': df['accuracy'].min(),
        'max_accuracy': df['accuracy'].max(),
        'q25_accuracy': df['accuracy'].quantile(0.25),
        'q75_accuracy': df['accuracy'].quantile(0.75)
    }
    
    print(f"\n🎯 ACCURACY METRICS:")
    print(f"   Mean Accuracy: {accuracy_stats['mean_accuracy']:.2f}%")
    print(f"   Median Accuracy: {accuracy_stats['median_accuracy']:.2f}%")
    print(f"   Standard Deviation: {accuracy_stats['std_accuracy']:.2f}%")
    print(f"   Min Accuracy: {accuracy_stats['min_accuracy']:.2f}%")
    print(f"   Max Accuracy: {accuracy_stats['max_accuracy']:.2f}%")
    print(f"   25th Percentile: {accuracy_stats['q25_accuracy']:.2f}%")
    print(f"   75th Percentile: {accuracy_stats['q75_accuracy']:.2f}%")
    
    # Error analysis
    if 'error' in df.columns:
        error_stats = {
            'mean_error': df['error'].mean(),
            'median_error': df['error'].median(),
            'mae': np.mean(np.abs(df['error'])),
            'rmse': np.sqrt(np.mean(df['error']**2)),
            'std_error': df['error'].std(),
            'min_error': df['error'].min(),
            'max_error': df['error'].max()
        }
        
        print(f"\n📏 ERROR ANALYSIS:")
        print(f"   Mean Error: {error_stats['mean_error']:.2f}m")
        print(f"   Median Error: {error_stats['median_error']:.2f}m")
        print(f"   Mean Absolute Error (MAE): {error_stats['mae']:.2f}m")
        print(f"   Root Mean Square Error (RMSE): {error_stats['rmse']:.2f}m")
        print(f"   Standard Deviation: {error_stats['std_error']:.2f}m")
        print(f"   Error Range: {error_stats['min_error']:.2f}m to {error_stats['max_error']:.2f}m")
    
    # Accuracy distribution
    accuracy_ranges = {
        'excellent': (df['accuracy'] >= 95).sum(),
        'very_good': ((df['accuracy'] >= 90) & (df['accuracy'] < 95)).sum(),
        'good': ((df['accuracy'] >= 80) & (df['accuracy'] < 90)).sum(),
        'fair': ((df['accuracy'] >= 70) & (df['accuracy'] < 80)).sum(),
        'poor': ((df['accuracy'] >= 50) & (df['accuracy'] < 70)).sum(),
        'very_poor': (df['accuracy'] < 50).sum()
    }
    
    print(f"\n📈 ACCURACY DISTRIBUTION:")
    print(f"   Excellent (≥95%): {accuracy_ranges['excellent']} waypoints ({accuracy_ranges['excellent']/len(df)*100:.1f}%)")
    print(f"   Very Good (90-94%): {accuracy_ranges['very_good']} waypoints ({accuracy_ranges['very_good']/len(df)*100:.1f}%)")
    print(f"   Good (80-89%): {accuracy_ranges['good']} waypoints ({accuracy_ranges['good']/len(df)*100:.1f}%)")
    print(f"   Fair (70-79%): {accuracy_ranges['fair']} waypoints ({accuracy_ranges['fair']/len(df)*100:.1f}%)")
    print(f"   Poor (50-69%): {accuracy_ranges['poor']} waypoints ({accuracy_ranges['poor']/len(df)*100:.1f}%)")
    print(f"   Very Poor (<50%): {accuracy_ranges['very_poor']} waypoints ({accuracy_ranges['very_poor']/len(df)*100:.1f}%)")
    
    # Distance correlation analysis
    correlation = df['actual_distance'].corr(df['simulated_distance'])
    print(f"\n🔗 CORRELATION ANALYSIS:")
    print(f"   Actual vs Simulated Distance Correlation: {correlation:.4f}")
    
    if 'calibrated_distance' in df.columns:
        calibrated_correlation = df['actual_distance'].corr(df['calibrated_distance'])
        print(f"   Actual vs Calibrated Distance Correlation: {calibrated_correlation:.4f}")
    
    # Best and worst waypoints
    best_waypoint = df.loc[df['accuracy'].idxmax()]
    worst_waypoint = df.loc[df['accuracy'].idxmin()]
    
    print(f"\n🏆 BEST PERFORMING WAYPOINT:")
    print(f"   Waypoint #{best_waypoint['waypoint']}: {best_waypoint['accuracy']:.2f}% accuracy")
    print(f"   Actual: {best_waypoint['actual_distance']:.2f}m, Simulated: {best_waypoint['simulated_distance']:.2f}m")
    
    print(f"\n⚠️ WORST PERFORMING WAYPOINT:")
    print(f"   Waypoint #{worst_waypoint['waypoint']}: {worst_waypoint['accuracy']:.2f}% accuracy")
    print(f"   Actual: {worst_waypoint['actual_distance']:.2f}m, Simulated: {worst_waypoint['simulated_distance']:.2f}m")
    
    # Overall assessment
    mean_acc = accuracy_stats['mean_accuracy']
    if mean_acc >= 90:
        assessment = "EXCELLENT"
        emoji = "🟢"
    elif mean_acc >= 80:
        assessment = "VERY GOOD"
        emoji = "🟡"
    elif mean_acc >= 70:
        assessment = "GOOD"
        emoji = "🟠"
    elif mean_acc >= 50:
        assessment = "FAIR"
        emoji = "🔴"
    else:
        assessment = "POOR"
        emoji = "⚫"
    
    print(f"\n🎯 OVERALL ASSESSMENT:")
    print(f"   {emoji} {assessment} - {mean_acc:.2f}% Mean Accuracy")
    
    # Compile results
    results = {
        'approach_name': approach_name,
        'total_waypoints': len(df),
        'timestamp': datetime.now().isoformat(),
        'accuracy_stats': accuracy_stats,
        'accuracy_ranges': accuracy_ranges,
        'correlation': correlation,
        'best_waypoint': {
            'waypoint': int(best_waypoint['waypoint']),
            'accuracy': float(best_waypoint['accuracy']),
            'actual_distance': float(best_waypoint['actual_distance']),
            'simulated_distance': float(best_waypoint['simulated_distance'])
        },
        'worst_waypoint': {
            'waypoint': int(worst_waypoint['waypoint']),
            'accuracy': float(worst_waypoint['accuracy']),
            'actual_distance': float(worst_waypoint['actual_distance']),
            'simulated_distance': float(worst_waypoint['simulated_distance'])
        },
        'overall_assessment': assessment,
        'mean_accuracy': mean_acc
    }
    
    if 'error' in df.columns:
        results['error_stats'] = error_stats
    
    if 'calibrated_distance' in df.columns:
        results['calibrated_correlation'] = calibrated_correlation
    
    return results

def create_visualizations(df, approach_name, output_dir="."):
    """
    Create comprehensive visualizations for distance accuracy analysis
    """
    print(f"\n📊 Creating visualizations for {approach_name}...")
    
    # Set style
    plt.style.use('default')
    sns.set_palette("husl")
    
    # Create figure with subplots
    fig = plt.figure(figsize=(20, 15))
    
    # 1. Accuracy Distribution Histogram
    plt.subplot(3, 4, 1)
    plt.hist(df['accuracy'], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
    plt.title(f'Accuracy Distribution\n{approach_name}')
    plt.xlabel('Accuracy (%)')
    plt.ylabel('Frequency')
    plt.axvline(df['accuracy'].mean(), color='red', linestyle='--', label=f'Mean: {df["accuracy"].mean():.1f}%')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 2. Actual vs Simulated Distance Scatter Plot
    plt.subplot(3, 4, 2)
    plt.scatter(df['actual_distance'], df['simulated_distance'], alpha=0.6, color='blue')
    min_val = min(df['actual_distance'].min(), df['simulated_distance'].min())
    max_val = max(df['actual_distance'].max(), df['simulated_distance'].max())
    plt.plot([min_val, max_val], [min_val, max_val], 'r--', label='Perfect Match')
    plt.xlabel('Actual Distance (m)')
    plt.ylabel('Simulated Distance (m)')
    plt.title('Actual vs Simulated Distance')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 3. Calibrated vs Actual Distance (if available)
    plt.subplot(3, 4, 3)
    if 'calibrated_distance' in df.columns:
        plt.scatter(df['actual_distance'], df['calibrated_distance'], alpha=0.6, color='green')
        plt.plot([min_val, max_val], [min_val, max_val], 'r--', label='Perfect Match')
        plt.xlabel('Actual Distance (m)')
        plt.ylabel('Calibrated Distance (m)')
        plt.title('Actual vs Calibrated Distance')
    else:
        plt.text(0.5, 0.5, 'No Calibrated Data', ha='center', va='center', transform=plt.gca().transAxes)
        plt.title('Calibrated Distance (N/A)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 4. Error Distribution
    plt.subplot(3, 4, 4)
    if 'error' in df.columns:
        plt.hist(df['error'], bins=20, alpha=0.7, color='orange', edgecolor='black')
        plt.title('Error Distribution')
        plt.xlabel('Error (m)')
        plt.ylabel('Frequency')
        plt.axvline(df['error'].mean(), color='red', linestyle='--', label=f'Mean: {df["error"].mean():.1f}m')
        plt.legend()
    else:
        plt.text(0.5, 0.5, 'No Error Data', ha='center', va='center', transform=plt.gca().transAxes)
        plt.title('Error Distribution (N/A)')
    plt.grid(True, alpha=0.3)
    
    # 5. Accuracy vs Waypoint
    plt.subplot(3, 4, 5)
    plt.plot(df['waypoint'], df['accuracy'], marker='o', markersize=4, linewidth=2)
    plt.title('Accuracy vs Waypoint')
    plt.xlabel('Waypoint Number')
    plt.ylabel('Accuracy (%)')
    plt.grid(True, alpha=0.3)
    
    # 6. Distance Comparison Over Waypoints
    plt.subplot(3, 4, 6)
    plt.plot(df['waypoint'], df['actual_distance'], label='Actual', marker='o', markersize=4)
    plt.plot(df['waypoint'], df['simulated_distance'], label='Simulated', marker='s', markersize=4)
    if 'calibrated_distance' in df.columns:
        plt.plot(df['waypoint'], df['calibrated_distance'], label='Calibrated', marker='^', markersize=4)
    plt.title('Distance Comparison Over Waypoints')
    plt.xlabel('Waypoint Number')
    plt.ylabel('Distance (m)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 7. Accuracy Box Plot
    plt.subplot(3, 4, 7)
    plt.boxplot(df['accuracy'], patch_artist=True, boxprops=dict(facecolor='lightblue'))
    plt.title('Accuracy Box Plot')
    plt.ylabel('Accuracy (%)')
    plt.grid(True, alpha=0.3)
    
    # 8. Cumulative Accuracy
    plt.subplot(3, 4, 8)
    sorted_acc = np.sort(df['accuracy'])
    cumulative = np.arange(1, len(sorted_acc) + 1) / len(sorted_acc) * 100
    plt.plot(sorted_acc, cumulative, linewidth=2)
    plt.title('Cumulative Accuracy Distribution')
    plt.xlabel('Accuracy (%)')
    plt.ylabel('Cumulative Percentage')
    plt.grid(True, alpha=0.3)
    
    # 9. Error vs Actual Distance
    plt.subplot(3, 4, 9)
    if 'error' in df.columns:
        plt.scatter(df['actual_distance'], df['error'], alpha=0.6, color='red')
        plt.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        plt.xlabel('Actual Distance (m)')
        plt.ylabel('Error (m)')
        plt.title('Error vs Actual Distance')
    else:
        plt.text(0.5, 0.5, 'No Error Data', ha='center', va='center', transform=plt.gca().transAxes)
        plt.title('Error vs Actual Distance (N/A)')
    plt.grid(True, alpha=0.3)
    
    # 10. Accuracy Heatmap (if waypoints are spatial)
    plt.subplot(3, 4, 10)
    if len(df) > 10:
        # Create a simple heatmap of accuracy values
        acc_matrix = df['accuracy'].values.reshape(-1, 1)
        sns.heatmap(acc_matrix.T, cmap='RdYlGn', cbar=True, xticklabels=False)
        plt.title('Accuracy Heatmap')
        plt.ylabel('Accuracy')
    else:
        plt.text(0.5, 0.5, 'Too Few Points\nfor Heatmap', ha='center', va='center', transform=plt.gca().transAxes)
        plt.title('Accuracy Heatmap (N/A)')
    
    # 11. Statistics Summary
    plt.subplot(3, 4, 11)
    plt.axis('off')
    stats_text = f"""
    STATISTICS SUMMARY
    
    Total Waypoints: {len(df)}
    Mean Accuracy: {df['accuracy'].mean():.2f}%
    Median Accuracy: {df['accuracy'].median():.2f}%
    Std Deviation: {df['accuracy'].std():.2f}%
    
    Min Accuracy: {df['accuracy'].min():.2f}%
    Max Accuracy: {df['accuracy'].max():.2f}%
    
    Actual Distance Range:
    {df['actual_distance'].min():.2f}m - {df['actual_distance'].max():.2f}m
    
    Simulated Distance Range:
    {df['simulated_distance'].min():.2f}m - {df['simulated_distance'].max():.2f}m
    """
    
    if 'error' in df.columns:
        stats_text += f"""
    
    Mean Absolute Error: {np.mean(np.abs(df['error'])):.2f}m
    Root Mean Square Error: {np.sqrt(np.mean(df['error']**2)):.2f}m
    """
    
    plt.text(0.05, 0.95, stats_text, transform=plt.gca().transAxes, 
             fontsize=10, verticalalignment='top', fontfamily='monospace')
    
    # 12. Approach Comparison (placeholder)
    plt.subplot(3, 4, 12)
    plt.text(0.5, 0.5, f'{approach_name}\nAnalysis Complete', 
             ha='center', va='center', transform=plt.gca().transAxes, 
             fontsize=14, fontweight='bold')
    plt.title('Analysis Status')
    
    plt.tight_layout()
    
    # Save the plot
    output_file = os.path.join(output_dir, f"{approach_name.lower().replace(' ', '_')}_distance_accuracy_analysis.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Visualization saved: {output_file}")
    
    plt.show()
    
    return output_file

def main():
    """Main function to analyze distance accuracy"""
    print("🔍 Distance Accuracy Analyzer")
    print("=" * 50)
    
    # List of available CSV files
    csv_files = [
        ("robust_fixed_distance_accuracy_analysis.csv", "Robust Fixed"),
        ("lane_based_distance_accuracy_analysis.csv", "Lane-Based"),
        ("calibrated_distance_accuracy_analysis.csv", "Calibrated"),
        ("realistic_speed_waypoint_analysis.csv", "Realistic Speed"),
        ("distance_accuracy_analysis.csv", "Enhanced Robust")
    ]
    
    print("\n📁 Available analysis files:")
    for i, (filename, approach) in enumerate(csv_files, 1):
        if os.path.exists(filename):
            print(f"   {i}. {filename} ({approach})")
        else:
            print(f"   {i}. {filename} ({approach}) - Not Found")
    
    # Get user input
    try:
        choice = input(f"\nSelect file to analyze (1-{len(csv_files)}) or 'all' for all files: ").strip()
        
        if choice.lower() == 'all':
            # Analyze all available files
            results = []
            for filename, approach in csv_files:
                if os.path.exists(filename):
                    print(f"\n{'='*60}")
                    result = analyze_distance_accuracy(filename, approach)
                    if result:
                        results.append(result)
                        
                        # Create visualizations
                        try:
                            df = pd.read_csv(filename)
                            create_visualizations(df, approach)
                        except Exception as e:
                            print(f"⚠️ Could not create visualizations: {e}")
            return results
        else:
            # Analyze single file
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(csv_files):
                filename, approach = csv_files[choice_idx]
                if os.path.exists(filename):
                    result = analyze_distance_accuracy(filename, approach)
                    if result:
                        # Create visualizations
                        try:
                            df = pd.read_csv(filename)
                            create_visualizations(df, approach)
                        except Exception as e:
                            print(f"⚠️ Could not create visualizations: {e}")
                    return result
                else:
                    print(f"❌ File not found: {filename}")
            else:
                print("❌ Invalid choice")
    except (ValueError, KeyboardInterrupt):
        print("\n❌ Analysis cancelled")
        return None

if __name__ == "__main__":
    main()
