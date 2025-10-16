#!/usr/bin/env python3
"""
Distance Accuracy Analysis and Visualization
Analyzes the results from V2V simulation distance accuracy analysis
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json
import os

def analyze_distance_accuracy():
    """Analyze distance accuracy results and create visualizations"""
    
    print("="*70)
    print("DISTANCE ACCURACY ANALYSIS & VISUALIZATION")
    print("="*70)
    
    # Check if analysis files exist
    analysis_file = 'distance_accuracy_analysis.csv'
    summary_file = 'distance_accuracy_summary.json'
    
    if not os.path.exists(analysis_file):
        print(f"❌ Analysis file not found: {analysis_file}")
        print("Please run v2v_simple_robust.py first to generate the analysis.")
        return
    
    # Load data
    print(f"\n📊 Loading analysis data from {analysis_file}...")
    df = pd.read_csv(analysis_file)
    print(f"✅ Loaded {len(df)} waypoints")
    
    # Load summary statistics
    if os.path.exists(summary_file):
        with open(summary_file, 'r') as f:
            summary = json.load(f)
        print(f"✅ Loaded summary statistics")
    else:
        summary = None
    
    # Basic statistics
    print(f"\n📊 Basic Statistics:")
    print(f"   Total waypoints: {len(df)}")
    print(f"   Actual distance range: {df['actual_distance'].min():.2f}m - {df['actual_distance'].max():.2f}m")
    print(f"   Simulated distance range: {df['simulated_distance'].min():.2f}m - {df['simulated_distance'].max():.2f}m")
    print(f"   Error range: {df['error'].min():.2f}m - {df['error'].max():.2f}m")
    print(f"   Accuracy range: {df['accuracy'].min():.2f}% - {df['accuracy'].max():.2f}%")
    
    # Create visualizations
    print(f"\n📈 Creating visualizations...")
    
    # Set up the plotting style
    plt.style.use('default')
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('V2V Simulation Distance Accuracy Analysis', fontsize=16, fontweight='bold')
    
    # 1. Actual vs Simulated Distance Scatter Plot
    ax1 = axes[0, 0]
    ax1.scatter(df['actual_distance'], df['simulated_distance'], alpha=0.7, s=50)
    
    # Add perfect correlation line
    min_dist = min(df['actual_distance'].min(), df['simulated_distance'].min())
    max_dist = max(df['actual_distance'].max(), df['simulated_distance'].max())
    ax1.plot([min_dist, max_dist], [min_dist, max_dist], 'r--', alpha=0.8, label='Perfect Correlation')
    
    ax1.set_xlabel('Actual Distance (m)')
    ax1.set_ylabel('Simulated Distance (m)')
    ax1.set_title('Actual vs Simulated Distance')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Calculate correlation coefficient
    correlation = df['actual_distance'].corr(df['simulated_distance'])
    ax1.text(0.05, 0.95, f'Correlation: {correlation:.3f}', 
             transform=ax1.transAxes, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # 2. Error Distribution Histogram
    ax2 = axes[0, 1]
    ax2.hist(df['error'], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
    ax2.axvline(df['error'].mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {df["error"].mean():.2f}m')
    ax2.set_xlabel('Error (m)')
    ax2.set_ylabel('Frequency')
    ax2.set_title('Error Distribution')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Accuracy by Waypoint
    ax3 = axes[1, 0]
    colors = ['green' if acc >= 70 else 'orange' if acc >= 0 else 'red' for acc in df['accuracy']]
    ax3.bar(df['waypoint'], df['accuracy'], color=colors, alpha=0.7)
    ax3.axhline(y=70, color='green', linestyle='--', alpha=0.8, label='Good Accuracy (70%)')
    ax3.axhline(y=0, color='red', linestyle='--', alpha=0.8, label='Poor Accuracy (0%)')
    ax3.set_xlabel('Waypoint Index')
    ax3.set_ylabel('Accuracy (%)')
    ax3.set_title('Accuracy by Waypoint')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Error Percentage Distribution
    ax4 = axes[1, 1]
    ax4.hist(df['error_percentage'], bins=20, alpha=0.7, color='lightcoral', edgecolor='black')
    ax4.axvline(df['error_percentage'].mean(), color='red', linestyle='--', linewidth=2, 
                label=f'Mean: {df["error_percentage"].mean():.1f}%')
    ax4.set_xlabel('Error Percentage (%)')
    ax4.set_ylabel('Frequency')
    ax4.set_title('Error Percentage Distribution')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save the plot
    plot_file = 'distance_accuracy_analysis.png'
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    print(f"✅ Visualization saved to: {plot_file}")
    
    # Create additional analysis plots
    create_additional_plots(df)
    
    # Print detailed analysis
    print_detailed_analysis(df, summary)
    
    plt.show()

def create_additional_plots(df):
    """Create additional specialized plots"""
    
    # Create a detailed accuracy analysis plot
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle('Detailed Distance Accuracy Analysis', fontsize=14, fontweight='bold')
    
    # 1. Distance comparison over waypoints
    ax1 = axes[0]
    ax1.plot(df['waypoint'], df['actual_distance'], 'b-o', label='Actual Distance', markersize=4)
    ax1.plot(df['waypoint'], df['simulated_distance'], 'r-s', label='Simulated Distance', markersize=4)
    ax1.set_xlabel('Waypoint Index')
    ax1.set_ylabel('Distance (m)')
    ax1.set_title('Distance Comparison Over Waypoints')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Cumulative accuracy
    ax2 = axes[1]
    sorted_df = df.sort_values('accuracy', ascending=False)
    cumulative_accuracy = sorted_df['accuracy'].cumsum() / range(1, len(sorted_df) + 1)
    ax2.plot(range(1, len(cumulative_accuracy) + 1), cumulative_accuracy, 'g-', linewidth=2)
    ax2.axhline(y=70, color='orange', linestyle='--', alpha=0.8, label='Good Accuracy Threshold')
    ax2.set_xlabel('Waypoints (sorted by accuracy)')
    ax2.set_ylabel('Cumulative Average Accuracy (%)')
    ax2.set_title('Cumulative Accuracy Analysis')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('detailed_accuracy_analysis.png', dpi=300, bbox_inches='tight')
    print(f"✅ Detailed analysis plot saved to: detailed_accuracy_analysis.png")

def print_detailed_analysis(df, summary):
    """Print detailed analysis results"""
    
    print(f"\n" + "="*70)
    print("DETAILED ANALYSIS RESULTS")
    print("="*70)
    
    # Accuracy categories
    high_acc = df[df['accuracy'] >= 90]
    medium_acc = df[(df['accuracy'] >= 70) & (df['accuracy'] < 90)]
    low_acc = df[df['accuracy'] < 70]
    
    print(f"\n📊 Accuracy Categories:")
    print(f"   High Accuracy (≥90%): {len(high_acc)} waypoints ({len(high_acc)/len(df)*100:.1f}%)")
    print(f"   Medium Accuracy (70-89%): {len(medium_acc)} waypoints ({len(medium_acc)/len(df)*100:.1f}%)")
    print(f"   Low Accuracy (<70%): {len(low_acc)} waypoints ({len(low_acc)/len(df)*100:.1f}%)")
    
    # Best and worst performers
    best_wp = df.loc[df['accuracy'].idxmax()]
    worst_wp = df.loc[df['accuracy'].idxmin()]
    
    print(f"\n📊 Best Performing Waypoint:")
    print(f"   Waypoint {best_wp['waypoint']}: Accuracy={best_wp['accuracy']:.2f}%")
    print(f"   Actual={best_wp['actual_distance']:.2f}m, Simulated={best_wp['simulated_distance']:.2f}m")
    print(f"   Error={best_wp['error']:.2f}m ({best_wp['error_percentage']:.2f}%)")
    
    print(f"\n📊 Worst Performing Waypoint:")
    print(f"   Waypoint {worst_wp['waypoint']}: Accuracy={worst_wp['accuracy']:.2f}%")
    print(f"   Actual={worst_wp['actual_distance']:.2f}m, Simulated={worst_wp['simulated_distance']:.2f}m")
    print(f"   Error={worst_wp['error']:.2f}m ({worst_wp['error_percentage']:.2f}%)")
    
    # Statistical measures
    print(f"\n📊 Statistical Measures:")
    print(f"   Mean Absolute Error: {df['error'].abs().mean():.2f} m")
    print(f"   Root Mean Square Error: {np.sqrt((df['error']**2).mean()):.2f} m")
    print(f"   Standard Deviation of Error: {df['error'].std():.2f} m")
    print(f"   Median Error: {df['error'].median():.2f} m")
    
    # Distance range analysis
    print(f"\n📊 Distance Range Analysis:")
    short_dist = df[df['actual_distance'] < 20]
    medium_dist = df[(df['actual_distance'] >= 20) & (df['actual_distance'] < 30)]
    long_dist = df[df['actual_distance'] >= 30]
    
    if len(short_dist) > 0:
        print(f"   Short distances (<20m): {len(short_dist)} waypoints, "
              f"Avg Accuracy: {short_dist['accuracy'].mean():.1f}%")
    if len(medium_dist) > 0:
        print(f"   Medium distances (20-30m): {len(medium_dist)} waypoints, "
              f"Avg Accuracy: {medium_dist['accuracy'].mean():.1f}%")
    if len(long_dist) > 0:
        print(f"   Long distances (≥30m): {len(long_dist)} waypoints, "
              f"Avg Accuracy: {long_dist['accuracy'].mean():.1f}%")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    if df['accuracy'].mean() < 50:
        print(f"   ⚠️ Overall accuracy is low ({df['accuracy'].mean():.1f}%). Consider:")
        print(f"      - Improving GPS-to-SUMO coordinate conversion")
        print(f"      - Using calibration factors")
        print(f"      - Checking network coverage")
    elif df['accuracy'].mean() < 70:
        print(f"   ⚠️ Moderate accuracy ({df['accuracy'].mean():.1f}%). Consider:")
        print(f"      - Fine-tuning route planning")
        print(f"      - Improving waypoint mapping")
    else:
        print(f"   ✅ Good accuracy ({df['accuracy'].mean():.1f}%)!")
    
    # Save detailed report
    report_file = 'distance_accuracy_report.txt'
    with open(report_file, 'w') as f:
        f.write("V2V Simulation Distance Accuracy Report\n")
        f.write("="*50 + "\n\n")
        f.write(f"Total waypoints analyzed: {len(df)}\n")
        f.write(f"Mean accuracy: {df['accuracy'].mean():.2f}%\n")
        f.write(f"Mean absolute error: {df['error'].abs().mean():.2f} m\n")
        f.write(f"Root mean square error: {np.sqrt((df['error']**2).mean()):.2f} m\n\n")
        
        f.write("Best waypoint: " + str(best_wp['waypoint']) + "\n")
        f.write("Worst waypoint: " + str(worst_wp['waypoint']) + "\n\n")
        
        f.write("Full data:\n")
        f.write(df.to_string(index=False))
    
    print(f"\n💾 Detailed report saved to: {report_file}")

if __name__ == "__main__":
    analyze_distance_accuracy()
