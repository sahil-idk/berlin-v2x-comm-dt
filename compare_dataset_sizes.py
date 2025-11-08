#!/usr/bin/env python3
"""
Compare V2V Digital Twin accuracy across different dataset sizes
Validates if 78-89% accuracy is consistent with more data points
"""

import pandas as pd
import matplotlib.pyplot as plt
import json
import os
import numpy as np
from datetime import datetime

def load_results(base_name):
    """Load CSV and JSON results for a specific dataset size"""
    csv_file = f'{base_name}_analysis.csv'
    json_file = f'{base_name}_summary.json'
    
    if not os.path.exists(csv_file):
        print(f"⚠️ Warning: {csv_file} not found")
        return None, None
    
    df = pd.read_csv(csv_file)
    
    summary = None
    if os.path.exists(json_file):
        with open(json_file, 'r') as f:
            summary = json.load(f)
    
    return df, summary

def analyze_accuracy_trends():
    """Analyze accuracy trends across different dataset sizes"""
    
    print("=" * 70)
    print("V2V DIGITAL TWIN - DATASET SIZE COMPARISON")
    print("=" * 70)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Define dataset configurations
    datasets = {
        '200 points': 'v2v_communication_200pts',
        '500 points': 'v2v_communication_500pts',
        '1000 points': 'v2v_communication_1000pts'
    }
    
    results = {}
    summaries = {}
    
    # Load all available results
    print("📂 Loading result files...\n")
    for name, base in datasets.items():
        df, summary = load_results(base)
        if df is not None:
            results[name] = df
            summaries[name] = summary
            print(f"✅ {name}: {len(df)} records loaded")
        else:
            print(f"❌ {name}: Not available")
    
    if len(results) == 0:
        print("\n❌ No result files found. Please run simulations first.")
        print("\nExpected files:")
        print("  - v2v_communication_200pts_analysis.csv")
        print("  - v2v_communication_500pts_analysis.csv")
        print("  - v2v_communication_1000pts_analysis.csv")
        return
    
    print("\n" + "=" * 70)
    print("ACCURACY COMPARISON")
    print("=" * 70)
    
    # Compare key metrics
    comparison_table = []
    
    for name, df in results.items():
        metrics = {
            'Dataset': name,
            'Waypoints': len(df),
            'Distance Acc (%)': df['distance_accuracy_pct'].mean(),
            'Distance Std (%)': df['distance_accuracy_pct'].std(),
            'Path Loss Acc (%)': df['path_loss_accuracy_pct'].mean() if 'path_loss_accuracy_pct' in df.columns else None,
            'SNR Acc (%)': df['snr_accuracy_pct'].mean() if 'snr_accuracy_pct' in df.columns else None,
            'PRR Acc (%)': df['prr_accuracy_pct'].mean() if 'prr_accuracy_pct' in df.columns else None,
            'RSRP Acc (%)': df['rsrp_accuracy_pct'].mean() if 'rsrp_accuracy_pct' in df.columns else None,
            'RSSI Acc (%)': df['rssi_accuracy_pct'].mean() if 'rssi_accuracy_pct' in df.columns else None,
        }
        comparison_table.append(metrics)
    
    # Print comparison table
    print("\n📊 Accuracy Metrics by Dataset Size:\n")
    for metrics in comparison_table:
        print(f"{metrics['Dataset']}:")
        print(f"  Waypoints: {metrics['Waypoints']}")
        print(f"  Distance Accuracy: {metrics['Distance Acc (%)']:.2f}% (±{metrics['Distance Std (%)']:.2f}%)")
        if metrics['Path Loss Acc (%)'] is not None:
            print(f"  Path Loss Accuracy: {metrics['Path Loss Acc (%)']:.2f}%")
        if metrics['SNR Acc (%)'] is not None:
            print(f"  SNR Accuracy: {metrics['SNR Acc (%)']:.2f}%")
        if metrics['PRR Acc (%)'] is not None:
            print(f"  PRR Accuracy: {metrics['PRR Acc (%)']:.2f}%")
        if metrics['RSRP Acc (%)'] is not None:
            print(f"  RSRP Accuracy: {metrics['RSRP Acc (%)']:.2f}%")
        if metrics['RSSI Acc (%)'] is not None:
            print(f"  RSSI Accuracy: {metrics['RSSI Acc (%)']:.2f}%")
        print()
    
    # Statistical analysis
    print("=" * 70)
    print("STATISTICAL ANALYSIS")
    print("=" * 70)
    
    dist_accuracies = [m['Distance Acc (%)'] for m in comparison_table]
    
    if len(dist_accuracies) >= 2:
        accuracy_change = dist_accuracies[-1] - dist_accuracies[0]
        print(f"\n📈 Distance Accuracy Trend:")
        print(f"  First: {dist_accuracies[0]:.2f}%")
        print(f"  Last: {dist_accuracies[-1]:.2f}%")
        print(f"  Change: {accuracy_change:+.2f}%")
        
        if abs(accuracy_change) < 3:
            print(f"  ✅ Accuracy is CONSISTENT across dataset sizes")
        elif accuracy_change > 0:
            print(f"  ✅ Accuracy IMPROVES with more data")
        else:
            print(f"  ⚠️ Accuracy DECREASES with more data")
    
    # Create visualizations
    print("\n" + "=" * 70)
    print("GENERATING VISUALIZATIONS")
    print("=" * 70)
    
    if len(results) >= 2:
        create_comparison_plots(results, comparison_table)
    else:
        print("\n⚠️ Need at least 2 datasets for meaningful plots")
    
    # Save comparison report
    save_comparison_report(comparison_table, summaries)
    
    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)

def create_comparison_plots(results, comparison_table):
    """Create comparison plots"""
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('V2V Digital Twin - Dataset Size Comparison', fontsize=16, fontweight='bold')
    
    # Plot 1: Distance Accuracy over Waypoint Index
    ax1 = axes[0, 0]
    for name, df in results.items():
        if 'waypoint' in df.columns and 'distance_accuracy_pct' in df.columns:
            ax1.plot(df['waypoint'], df['distance_accuracy_pct'], 
                    label=name, alpha=0.7, linewidth=1.5)
    ax1.set_xlabel('Waypoint Index')
    ax1.set_ylabel('Distance Accuracy (%)')
    ax1.set_title('Distance Accuracy Across Waypoints')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim([0, 100])
    
    # Plot 2: Mean Accuracy by Dataset Size
    ax2 = axes[0, 1]
    datasets_names = [m['Dataset'] for m in comparison_table]
    dist_accs = [m['Distance Acc (%)'] for m in comparison_table]
    colors = ['#3498db', '#e74c3c', '#2ecc71'][:len(datasets_names)]
    bars = ax2.bar(datasets_names, dist_accs, color=colors, alpha=0.7)
    ax2.set_ylabel('Mean Distance Accuracy (%)')
    ax2.set_title('Mean Distance Accuracy by Dataset Size')
    ax2.set_ylim([0, 100])
    ax2.axhline(y=78, color='green', linestyle='--', alpha=0.5, label='Target: 78%')
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%', ha='center', va='bottom', fontweight='bold')
    
    # Plot 3: Communication Parameter Accuracy
    ax3 = axes[1, 0]
    
    # Collect all communication metrics
    comm_metrics = ['Path Loss Acc (%)', 'SNR Acc (%)', 'PRR Acc (%)']
    comm_labels = ['Path Loss', 'SNR', 'PRR']
    
    x = np.arange(len(comm_labels))
    width = 0.25
    
    for i, (name, df) in enumerate(results.items()):
        values = []
        for metric in comm_metrics:
            if metric in comparison_table[i]:
                val = comparison_table[i][metric]
                values.append(val if val is not None else 0)
            else:
                values.append(0)
        
        ax3.bar(x + i * width, values, width, label=name, alpha=0.7)
    
    ax3.set_ylabel('Accuracy (%)')
    ax3.set_title('Communication Parameter Accuracy')
    ax3.set_xticks(x + width)
    ax3.set_xticklabels(comm_labels)
    ax3.legend()
    ax3.grid(True, alpha=0.3, axis='y')
    ax3.set_ylim([0, 100])
    
    # Plot 4: Accuracy Distribution (Box Plot)
    ax4 = axes[1, 1]
    
    data_for_boxplot = []
    labels_for_boxplot = []
    
    for name, df in results.items():
        if 'distance_accuracy_pct' in df.columns:
            data_for_boxplot.append(df['distance_accuracy_pct'])
            labels_for_boxplot.append(name)
    
    if data_for_boxplot:
        bp = ax4.boxplot(data_for_boxplot, labels=labels_for_boxplot, patch_artist=True)
        for patch, color in zip(bp['boxes'], colors[:len(bp['boxes'])]):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        ax4.set_ylabel('Distance Accuracy (%)')
        ax4.set_title('Distance Accuracy Distribution')
        ax4.grid(True, alpha=0.3, axis='y')
        ax4.set_ylim([0, 100])
    
    plt.tight_layout()
    
    output_file = 'dataset_size_comparison.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Plot saved: {output_file}")
    
    plt.close()

def save_comparison_report(comparison_table, summaries):
    """Save comparison report to JSON"""
    
    report = {
        'analysis_date': datetime.now().isoformat(),
        'datasets_compared': len(comparison_table),
        'metrics': comparison_table,
        'summaries': summaries,
        'conclusion': generate_conclusion(comparison_table)
    }
    
    output_file = 'dataset_size_comparison_report.json'
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Report saved: {output_file}")
    
    # Also save as readable text
    text_file = 'dataset_size_comparison_report.txt'
    with open(text_file, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("V2V DIGITAL TWIN - DATASET SIZE COMPARISON REPORT\n")
        f.write("=" * 70 + "\n")
        f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for metrics in comparison_table:
            f.write(f"{metrics['Dataset']}:\n")
            for key, value in metrics.items():
                if key != 'Dataset' and value is not None:
                    if isinstance(value, float):
                        f.write(f"  {key}: {value:.2f}\n")
                    else:
                        f.write(f"  {key}: {value}\n")
            f.write("\n")
        
        f.write("=" * 70 + "\n")
        f.write("CONCLUSION\n")
        f.write("=" * 70 + "\n")
        f.write(report['conclusion'] + "\n")
    
    print(f"✅ Text report saved: {text_file}")

def generate_conclusion(comparison_table):
    """Generate conclusion based on comparison"""
    
    if len(comparison_table) < 2:
        return "Insufficient data for comparison."
    
    dist_accs = [m['Distance Acc (%)'] for m in comparison_table]
    first_acc = dist_accs[0]
    last_acc = dist_accs[-1]
    change = last_acc - first_acc
    
    conclusion = f"Comparing {comparison_table[0]['Dataset']} to {comparison_table[-1]['Dataset']}:\n"
    conclusion += f"- Distance accuracy changed from {first_acc:.2f}% to {last_acc:.2f}% ({change:+.2f}%)\n"
    
    if abs(change) < 3:
        conclusion += "- ✅ Digital Twin shows CONSISTENT accuracy across dataset sizes\n"
        conclusion += "- This validates the robustness of the simulation approach\n"
    elif change > 3:
        conclusion += "- ✅ Digital Twin shows IMPROVED accuracy with more data\n"
        conclusion += "- Larger datasets provide better validation coverage\n"
    else:
        conclusion += "- ⚠️ Digital Twin shows DECREASED accuracy with more data\n"
        conclusion += "- May indicate edge cases or specific waypoint challenges\n"
    
    # Check if accuracy meets target
    if last_acc >= 78:
        conclusion += f"- ✅ Target accuracy (78%) ACHIEVED: {last_acc:.2f}%\n"
    else:
        conclusion += f"- ⚠️ Target accuracy (78%) NOT MET: {last_acc:.2f}%\n"
    
    return conclusion

if __name__ == "__main__":
    analyze_accuracy_trends()

