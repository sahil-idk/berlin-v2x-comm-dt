#!/usr/bin/env python3
"""
Calculate Overall Accuracy from Calibrated Distance Analysis
"""

import pandas as pd
import numpy as np

def calculate_overall_accuracy():
    """Calculate and display overall accuracy metrics"""
    
    print("=" * 70)
    print("OVERALL ACCURACY CALCULATION")
    print("=" * 70)
    
    # Load CSV
    df = pd.read_csv('calibrated_distance_accuracy_analysis.csv')
    
    print(f"\n📊 Dataset Summary:")
    print(f"   Total Waypoints: {len(df)}")
    print(f"   Calibration Factor: 0.607")
    
    # Accuracy Statistics
    print(f"\n📊 Accuracy Statistics:")
    print(f"   Mean Accuracy: {df['accuracy'].mean():.2f}%")
    print(f"   Median Accuracy: {df['accuracy'].median():.2f}%")
    print(f"   Std Dev: {df['accuracy'].std():.2f}%")
    print(f"   Min Accuracy: {df['accuracy'].min():.2f}%")
    print(f"   Max Accuracy: {df['accuracy'].max():.2f}%")
    
    # Error Statistics
    print(f"\n📊 Error Statistics:")
    print(f"   Mean Error: {df['error'].mean():.2f} m")
    print(f"   Mean Absolute Error: {df['error'].abs().mean():.2f} m")
    print(f"   Root Mean Square Error: {np.sqrt((df['error']**2).mean()):.2f} m")
    print(f"   Std Dev Error: {df['error'].std():.2f} m")
    
    # Distance Statistics
    print(f"\n📊 Distance Statistics:")
    print(f"   Actual Distance Range: {df['actual_distance'].min():.2f}m - {df['actual_distance'].max():.2f}m")
    print(f"   Simulated Distance Range: {df['simulated_distance'].min():.2f}m - {df['simulated_distance'].max():.2f}m")
    print(f"   Mean Actual Distance: {df['actual_distance'].mean():.2f} m")
    print(f"   Mean Simulated Distance: {df['simulated_distance'].mean():.2f} m")
    
    # Accuracy Distribution
    high_accuracy = (df['accuracy'] >= 90).sum()
    medium_accuracy = ((df['accuracy'] >= 70) & (df['accuracy'] < 90)).sum()
    low_accuracy = (df['accuracy'] < 70).sum()
    
    print(f"\n📊 Accuracy Distribution:")
    print(f"   High Accuracy (≥90%): {high_accuracy} waypoints ({high_accuracy/len(df)*100:.1f}%)")
    print(f"   Medium Accuracy (70-89%): {medium_accuracy} waypoints ({medium_accuracy/len(df)*100:.1f}%)")
    print(f"   Low Accuracy (<70%): {low_accuracy} waypoints ({low_accuracy/len(df)*100:.1f}%)")
    
    # Error Percentage Distribution
    print(f"\n📊 Error Percentage Distribution:")
    error_pct = df['error_percentage'].abs()
    print(f"   <10% error: {(error_pct < 10).sum()} waypoints ({(error_pct < 10).sum()/len(df)*100:.1f}%)")
    print(f"   10-25% error: {((error_pct >= 10) & (error_pct < 25)).sum()} waypoints ({((error_pct >= 10) & (error_pct < 25)).sum()/len(df)*100:.1f}%)")
    print(f"   25-50% error: {((error_pct >= 25) & (error_pct < 50)).sum()} waypoints ({((error_pct >= 25) & (error_pct < 50)).sum()/len(df)*100:.1f}%)")
    print(f"   >50% error: {(error_pct >= 50).sum()} waypoints ({(error_pct >= 50).sum()/len(df)*100:.1f}%)")
    
    # Best and Worst Waypoints
    best_idx = df['accuracy'].idxmax()
    worst_idx = df['accuracy'].idxmin()
    
    print(f"\n📊 Best Waypoint:")
    print(f"   Waypoint #{df.loc[best_idx, 'waypoint']}")
    print(f"   Actual: {df.loc[best_idx, 'actual_distance']:.2f}m")
    print(f"   Simulated: {df.loc[best_idx, 'simulated_distance']:.2f}m")
    print(f"   Error: {df.loc[best_idx, 'error']:.2f}m ({df.loc[best_idx, 'error_percentage']:.2f}%)")
    print(f"   Accuracy: {df.loc[best_idx, 'accuracy']:.2f}%")
    
    print(f"\n📊 Worst Waypoint:")
    print(f"   Waypoint #{df.loc[worst_idx, 'waypoint']}")
    print(f"   Actual: {df.loc[worst_idx, 'actual_distance']:.2f}m")
    print(f"   Simulated: {df.loc[worst_idx, 'simulated_distance']:.2f}m")
    print(f"   Error: {df.loc[worst_idx, 'error']:.2f}m ({df.loc[worst_idx, 'error_percentage']:.2f}%)")
    print(f"   Accuracy: {df.loc[worst_idx, 'accuracy']:.2f}%")
    
    # Overall Assessment
    print(f"\n" + "=" * 70)
    print("OVERALL ASSESSMENT")
    print("=" * 70)
    
    mean_acc = df['accuracy'].mean()
    if mean_acc >= 80:
        assessment = "EXCELLENT ✅"
    elif mean_acc >= 60:
        assessment = "GOOD ✓"
    elif mean_acc >= 40:
        assessment = "FAIR ⚠️"
    else:
        assessment = "NEEDS IMPROVEMENT ❌"
    
    print(f"\n📊 Overall Accuracy: {mean_acc:.2f}% - {assessment}")
    print(f"📊 Mean Absolute Error: {df['error'].abs().mean():.2f} m")
    print(f"📊 Calibration Applied: YES (Factor: 0.607)")
    
    # Save summary (convert numpy types to Python types for JSON)
    summary = {
        'total_waypoints': int(len(df)),
        'mean_accuracy': float(mean_acc),
        'median_accuracy': float(df['accuracy'].median()),
        'mean_absolute_error': float(df['error'].abs().mean()),
        'rmse': float(np.sqrt((df['error']**2).mean())),
        'high_accuracy_count': int(high_accuracy),
        'medium_accuracy_count': int(medium_accuracy),
        'low_accuracy_count': int(low_accuracy),
        'assessment': str(assessment)
    }
    
    import json
    with open('overall_accuracy_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n💾 Summary saved to: overall_accuracy_summary.json")
    print("=" * 70)

if __name__ == "__main__":
    calculate_overall_accuracy()

