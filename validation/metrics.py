#!/usr/bin/env python3
"""
Validation metrics for digital twin V2V simulation
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import math

class ValidationMetrics:
    """Calculate validation metrics for distance accuracy and communication"""
    
    def __init__(self, calibration_factor: float = 0.607):
        self.calibration_factor = calibration_factor
    
    def calculate_distance_accuracy(self, evaluation_data: List[Dict], 
                                  dataset_distances: np.ndarray) -> Dict:
        """Calculate distance accuracy metrics"""
        
        if not evaluation_data:
            return {'error': 'No evaluation data'}
        
        errors = []
        error_percentages = []
        calibrated_distances = []
        
        for i, eval_point in enumerate(evaluation_data):
            if i >= len(dataset_distances):
                break
                
            calibrated_dist = eval_point['distance_info']['calibrated_distance']
            expected_dist = dataset_distances[i]
            
            if expected_dist > 0:
                error = abs(calibrated_dist - expected_dist)
                error_percentage = (error / expected_dist) * 100
                
                errors.append(error)
                error_percentages.append(error_percentage)
                calibrated_distances.append(calibrated_dist)
        
        if not errors:
            return {'error': 'No valid distance comparisons'}
        
        metrics = {
            'total_validations': len(errors),
            'mean_error': np.mean(errors),
            'median_error': np.median(errors),
            'std_error': np.std(errors),
            'mean_error_percentage': np.mean(error_percentages),
            'median_error_percentage': np.median(error_percentages),
            'std_error_percentage': np.std(error_percentages),
            'min_error_percentage': np.min(error_percentages),
            'max_error_percentage': np.max(error_percentages),
            'distance_range': {
                'min_calibrated': np.min(calibrated_distances),
                'max_calibrated': np.max(calibrated_distances),
                'min_expected': np.min(dataset_distances[:len(calibrated_distances)]),
                'max_expected': np.max(dataset_distances[:len(calibrated_distances)])
            },
            'calibration_factor': self.calibration_factor
        }
        
        return metrics
    
    def calculate_communication_metrics(self, snr_data: List[float]) -> Dict:
        """Calculate communication performance metrics"""
        
        if not snr_data:
            return {'error': 'No SNR data'}
        
        # Communication success threshold (SNR > 5 dB)
        success_threshold = 5.0
        successful_communications = [snr > success_threshold for snr in snr_data]
        
        metrics = {
            'total_measurements': len(snr_data),
            'mean_snr': np.mean(snr_data),
            'median_snr': np.median(snr_data),
            'std_snr': np.std(snr_data),
            'min_snr': np.min(snr_data),
            'max_snr': np.max(snr_data),
            'communication_success_rate': np.mean(successful_communications) * 100,
            'successful_communications': sum(successful_communications),
            'success_threshold': success_threshold
        }
        
        return metrics
    
    def generate_validation_summary(self, distance_metrics: Dict, 
                                  comm_metrics: Dict) -> str:
        """Generate validation summary text"""
        
        summary = "DIGITAL TWIN V2V VALIDATION SUMMARY\n"
        summary += "=" * 40 + "\n\n"
        
        # Distance accuracy
        if 'error' not in distance_metrics:
            summary += "DISTANCE ACCURACY:\n"
            summary += f"  Total validations: {distance_metrics['total_validations']}\n"
            summary += f"  Mean error: {distance_metrics['mean_error']:.2f}m\n"
            summary += f"  Mean error percentage: {distance_metrics['mean_error_percentage']:.1f}%\n"
            summary += f"  Error range: {distance_metrics['min_error_percentage']:.1f}% - {distance_metrics['max_error_percentage']:.1f}%\n"
            summary += f"  Calibration factor: {distance_metrics['calibration_factor']}\n"
            summary += f"  Distance range: {distance_metrics['distance_range']['min_calibrated']:.1f}m - {distance_metrics['distance_range']['max_calibrated']:.1f}m\n\n"
        else:
            summary += f"DISTANCE ACCURACY: {distance_metrics['error']}\n\n"
        
        # Communication performance
        if 'error' not in comm_metrics:
            summary += "COMMUNICATION PERFORMANCE:\n"
            summary += f"  Total measurements: {comm_metrics['total_measurements']}\n"
            summary += f"  Mean SNR: {comm_metrics['mean_snr']:.1f}dB\n"
            summary += f"  SNR range: {comm_metrics['min_snr']:.1f}dB - {comm_metrics['max_snr']:.1f}dB\n"
            summary += f"  Communication success rate: {comm_metrics['communication_success_rate']:.1f}%\n"
            summary += f"  Successful communications: {comm_metrics['successful_communications']}/{comm_metrics['total_measurements']}\n\n"
        else:
            summary += f"COMMUNICATION PERFORMANCE: {comm_metrics['error']}\n\n"
        
        # Overall assessment
        if 'error' not in distance_metrics and 'error' not in comm_metrics:
            if distance_metrics['mean_error_percentage'] < 5.0:
                summary += "OVERALL ASSESSMENT: ✅ EXCELLENT\n"
            elif distance_metrics['mean_error_percentage'] < 10.0:
                summary += "OVERALL ASSESSMENT: ✅ GOOD\n"
            elif distance_metrics['mean_error_percentage'] < 20.0:
                summary += "OVERALL ASSESSMENT: ⚠️  ACCEPTABLE\n"
            else:
                summary += "OVERALL ASSESSMENT: ❌ POOR\n"
        
        return summary
    
    def export_evaluation_csv(self, evaluation_data: List[Dict], 
                            dataset_distances: np.ndarray,
                            output_file: str) -> bool:
        """Export evaluation data to CSV"""
        
        try:
            rows = []
            
            for i, eval_point in enumerate(evaluation_data):
                if i >= len(dataset_distances):
                    break
                
                row = {
                    'timestamp': eval_point['timestamp'],
                    'sim_time': eval_point['sim_time'],
                    'data_index': eval_point['data_index'],
                    'expected_distance': dataset_distances[i],
                    'raw_distance': eval_point['distance_info']['raw_distance'],
                    'calibrated_distance': eval_point['distance_info']['calibrated_distance'],
                    'error': abs(eval_point['distance_info']['calibrated_distance'] - dataset_distances[i]),
                    'error_percentage': abs(eval_point['distance_info']['calibrated_distance'] - dataset_distances[i]) / dataset_distances[i] * 100 if dataset_distances[i] > 0 else 0
                }
                
                # Add position data if available
                if 'positions' in eval_point and eval_point['positions']:
                    src_pos = eval_point['positions'].get('source')
                    dst_pos = eval_point['positions'].get('destination')
                    
                    if src_pos:
                        row['src_x'] = src_pos[0]
                        row['src_y'] = src_pos[1]
                    if dst_pos:
                        row['dst_x'] = dst_pos[0]
                        row['dst_y'] = dst_pos[1]
                
                rows.append(row)
            
            df = pd.DataFrame(rows)
            df.to_csv(output_file, index=False)
            
            print(f"✅ Evaluation data exported to {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to export evaluation data: {e}")
            return False
