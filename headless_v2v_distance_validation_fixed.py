#!/usr/bin/env python3
"""
Headless V2V Distance Validation

This script validates distance accuracy between vehicles by:
1. Selecting 10 representative timestamps from the sidelink dataset
2. Running headless SUMO simulations for each timestamp
3. Computing simulated inter-vehicle distances
4. Comparing with actual distances from the dataset
5. Reporting accuracy metrics
"""

import traci
import pandas as pd
import numpy as np
import math
import json
import subprocess
import os
from datetime import datetime
from typing import List, Tuple, Dict, Optional

class HeadlessV2VDistanceValidator:
    """Validates V2V distance accuracy using headless SUMO simulations"""
    
    def __init__(self, config_path: str = "osm_headless.sumocfg"):
        """
        Initialize the validator
        
        Args:
            config_path: Path to SUMO configuration file
        """
        self.config_path = config_path
        self.results = []
        self.sumo_process = None
        
    def start_headless_sumo(self) -> bool:
        """Start SUMO in headless mode"""
        try:
            # Create headless command - remove GUI settings
            sumo_cmd = [
                "sumo",  # Use 'sumo' instead of 'sumo-gui' for headless
                "-c", self.config_path,
                "--no-step-log",
                "--ignore-route-errors",
                "--fcd-output", "validation_fcd.xml",  # For position tracking
                "--verbose"
            ]
            
            print(f"🚀 Starting headless SUMO with command: {' '.join(sumo_cmd)}")
            traci.start(sumo_cmd)
            
            # Wait a moment for connection to establish
            import time
            time.sleep(2)
            return True
            
        except Exception as e:
            print(f"❌ Failed to start headless SUMO: {e}")
            return False
    
    def stop_sumo(self):
        """Stop SUMO and cleanup"""
        try:
            traci.close()
            print("✅ SUMO simulation stopped")
        except Exception as e:
            print(f"⚠️  Error stopping SUMO: {e}")
    
    def gps_to_sumo_coordinates(self, lat: float, lon: float) -> Optional[Tuple[float, float]]:
        """Convert GPS coordinates to SUMO coordinates"""
        try:
            # Try sumolib first for better accuracy
            try:
                from sumolib import net
                net_file = net.readNet('osm.net.xml.gz')
                x, y = net_file.convertLonLat2XY(lon, lat)
                return x, y
            except ImportError:
                # Fallback to traci
                x, y = traci.simulation.convertGeo(lon, lat)
                return x, y
        except Exception as e:
            print(f"❌ GPS conversion failed for ({lat}, {lon}): {e}")
            return None
    
    def find_closest_edge_to_position(self, x: float, y: float, max_distance: float = 1000) -> Optional[str]:
        """Find edge closest to given SUMO position"""
        min_distance = float('inf')
        closest_edge = None
        
        for edge_id in traci.edge.getIDList():
        # Skip internal edges
            if edge_id.startswith(':') or edge_id.startswith('-'):
                continue
                
            try:
                from_junction = traci.edge.getFromJunction(edge_id)
                from_pos = traci.junction.getPosition(from_junction)
                
                distance = math.sqrt((x - from_pos[0])**2 + (y - from_pos[1])**2)
                
                if distance < min_distance and distance < max_distance:
                    min_distance = distance
                    closest_edge = edge_id
                    
            except:
                continue
                
        if closest_edge:
            return closest_edge
        return None
    
    def calculate_gps_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two GPS coordinates using Haversine formula"""
        R = 6371000  # Earth radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) * math.sin(delta_lat / 2) +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) * math.sin(delta_lon / 2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        
        return distance
    
    def simulate_vehicle_pair(self, 
                             src_lat: float, src_lon: float,
                             dst_lat: float, dst_lon: float,
                             expected_distance: float) -> Dict:
        """
        Simulate a vehicle pair and compute distance
        
        Args:
            src_lat, lon: Source vehicle GPS coordinates
            dst_lat, lon: Destination vehicle GPS coordinates
            expected_distance: Actual distance from dataset
            
        Returns:
            Dictionary with simulation results
        """
        result = {
            'success': False,
            'expected_distance': expected_distance,
            'simulated_distance': None,
            'error': None,
            'error_percentage': None,
            'src_coords': (src_lat, src_lon),
            'dst_coords': (dst_lat, dst_lon),
            'src_sumo_coords': None,
            'dst_sumo_coords': None,
            'src_edge': None,
            'dst_edge': None
        }
        
        print(f"\n🔄 Simulating vehicle pair:")
        print(f"   Source: ({src_lat:.6f}, {src_lon:.6f})")
        print(f"   Dest: ({dst_lat:.6f}, {dst_lon:.6f})")
        print(f"   Expected distance: {expected_distance:.2f}m")
        
        # Convert GPS to SUMO coordinates
        src_x, src_y = self.gps_to_sumo_coordinates(src_lat, src_lon)
        dst_x, dst_y = self.gps_to_sumo_coordinates(dst_lat, dst_lon)
        
        if not all([src_x, src_y, dst_x, dst_y]):
            print("❌ GPS conversion failed")
            return result
        
        result['src_sumo_coords'] = (src_x, src_y)
        result['dst_sumo_coords'] = (dst_x, dst_y)
        
        print(f"   SUMO Source: ({src_x:.2f}, {src_y:.2f})")
        print(f"   SUMO Dest: ({dst_x:.2f}, {dst_y:.2f})")
        
        # Find closest edges
        src_edge = self.find_closest_edge_to_position(src_x, src_y)
        dst_edge = self.find_closest_edge_to_position(dst_x, dst_y)
        
        if not src_edge or not dst_edge:
            print("❌ Edge mapping failed")
            return result
        
        result['src_edge'] = src_edge
        result['dst_edge'] = dst_edge
        
        print(f"   Source edge: {src_edge}")
        print(f"   Destination edge: {dst_edge}")
        
        # Calculate Euclidean distance in SUMO coordinates
        simulated_distance = math.sqrt((dst_x - src_x)**2 + (dst_y - src_y)**2)
        result['simulated_distance'] = simulated_distance
        result['success'] = True
        
        # Calculate error
        error = abs(simulated_distance - expected_distance)
        error_percentage = (error / expected_distance) * 100 if expected_distance > 0 else 0
        
        result['error'] = error
        result['error_percentage'] = error_percentage
        
        print(f"   Simulated distance: {simulated_distance:.2f}m")
        print(f"   Error: {error:.2f}m ({error_percentage:.1f}%)")
        
        return result
    
    def select_representative_timestamps(self, df: pd.DataFrame, num_samples: int = 10) -> List[pd.Series]:
        """Select representative timestamps from the dataset"""
        print(f"\n📊 Selecting {num_samples} representative timestamps...")
        
        # Filter for valid data (complete GPS information)
        valid_df = df.dropna(subset=[
            'Latitude_source', 'Longitude_source',
            'Latitude_destination', 'Longitude_destination',
            'distance'
        ])
        
        print(f"   Valid records: {len(valid_df)}")
        
        # Sort by timestamp and select evenly distributed samples
        valid_df_sorted = valid_df.sort_values('timestamp')
        
        # Select evenly distributed timestamps
        indices = np.linspace(0, len(valid_df_sorted) - 1, num_samples, dtype=int)
        selected_rows = valid_df_sorted.iloc[indices]
        
        print(f"   Selected timestamps: {selected_rows['timestamp'].values.tolist()}")
        
        return [row for _, row in selected_rows.iterrows()]
    
    def validate_distances(self, max_samples: int = 10) -> Dict:
        """Main validation method"""
        print("🚀 Starting Headless V2V Distance Validation")
        print("=" * 60)
        
        # Load dataset
        print("\n📋 Loading sidelink dataset...")
        try:
            df = pd.read_csv('sidelink_parsed.csv')
            print(f"   Loaded {len(df)} records")
        except Exception as e:
            print(f"❌ Failed to load dataset: {e}")
            return {}
        
        # Select representative timestamps
        sample_rows = self.select_representative_timestamps(df, max_samples)
        
        # Start headless SUMO
        if not self.start_headless_sumo():
            print("❌ Cannot proceed without SUMO")
            return {}
        
        try:
            # Validate each sample
            validation_results = []
            
            for i, row in enumerate(sample_rows):
                print(f"\n📐 Validating sample {i+1}/{len(sample_rows)}")
                
                result = self.simulate_vehicle_pair(
                    row['Latitude_source'], row['Longitude_source'],
                    row['Latitude_destination'], row['Longitude_destination'],
                    row['distance']
                )
                
                # Add metadata
                result['timestamp'] = row['timestamp']
                result['timestamp_iso'] = row.get('timestamp_iso', 'N/A')
                result['source_device'] = row.get('Source', 'N/A')
                result['dest_device'] = row.get('Destination', 'N/A')
                result['sample_id'] = i + 1
                
                validation_results.append(result)
            
            # Analyze results
            analysis = self.analyze_results(validation_results)
            
            # Save results
            self.save_results(validation_results, analysis)
            
            return analysis
            
        finally:
            self.stop_sumo()
    
    def analyze_results(self, results: List[Dict]) -> Dict:
        """Analyze validation results"""
        print("\n📊 Analyzing Results")
        print("-" * 30)
        
        successful_results = [r for r in results if r['success']]
        failed_count = len(results) - len(successful_results)
        
        if not successful_results:
            print("❌ No successful validations")
            return {}
        
        errors = [r['error'] for r in successful_results]
        error_percentages = [r['error_percentage'] for r in successful_results]
        expected_distances = [r['expected_distance'] for r in successful_results]
        simulated_distances = [r['simulated_distance'] for r in successful_results]
        
        analysis = {
            'total_samples': len(results),
            'successful_validations': len(successful_results),
            'failed_validations': failed_count,
            'success_rate': len(successful_results) / len(results) * 100,
            'statistics': {
                'mean_error': np.mean(errors),
                'median_error': np.median(errors),
                'std_error': np.std(errors),
                'min_error': np.min(errors),
                'max_error': np.max(errors),
                'mean_error_percentage': np.mean(error_percentages),
                'median_error_percentage': np.median(error_percentages),
                'std_error_percentage': np.std(error_percentages),
                'min_error_percentage': np.min(error_percentages),
                'max_error_percentage': np.max(error_percentages)
            },
            'distance_ranges': {
                'expected_distances': {
                    'min': np.min(expected_distances),
                    'max': np.max(expected_distances),
                    'mean': np.mean(expected_distances),
                    'std': np.std(expected_distances)
                },
                'simulated_distances': {
                    'min': np.min(simulated_distances),
                    'max': np.max(simulated_distances),
                    'mean': np.mean(simulated_distances),
                    'std': np.std(simulated_distances)
                }
            }
        }
        
        # Print summary
        print(f"✅ Successful validations: {analysis['successful_validations']}/{analysis['total_samples']}")
        print(f"   Success rate: {analysis['success_rate']:.1f}%")
        print(f"📏 Distance accuracy:")
        print(f"   Mean error: {analysis['statistics']['mean_error']:.2f}m")
        print(f"   Mean error percentage: {analysis['statistics']['mean_error_percentage']:.1f}%")
        print(f"   Error range: {analysis['statistics']['min_error']:.2f}m to {analysis['statistics']['max_error']:.2f}m")
        
        return analysis
    
    def save_results(self, results: List[Dict], analysis: Dict):
        """Save validation results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed results
        results_file = f"distance_validation_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump({
                'results': results,
                'analysis': analysis,
                'timestamp': timestamp
            }, f, indent=2)
        
        # Save summary report
        summary_file = f"distance_validation_summary_{timestamp}.txt"
        with open(summary_file, 'w') as f:
            f.write("HEADLESS V2V DISTANCE VALIDATION SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Validation completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total samples: {analysis.get('total_samples', 0)}\n")
            f.write(f"Successful validations: {analysis.get('successful_validations', 0)}\n")
            f.write(f"Success rate: {analysis.get('success_rate', 0):.1f}%\n\n")
            
            if 'statistics' in analysis:
                stats = analysis['statistics']
                f.write("ACCURACY STATISTICS\n")
                f.write("-" * 20 + "\n")
                f.write(f"Mean error: {stats['mean_error']:.2f}m ({stats['mean_error_percentage']:.1f}%)\n")
                f.write(f"Median error: {stats['median_error']:.2f}m ({stats['median_error_percentage']:.1f}%)\n")
                f.write(f"Error std dev: {stats['std_error']:.2f}m ({stats['std_error_percentage']:.1f}%)\n")
                f.write(f"Min error: {stats['min_error']:.2f}m ({stats['min_error_percentage']:.1f}%)\n")
                f.write(f"Max error: {stats['max_error']:.2f}m ({stats['max_error_percentage']:.1f}%)\n")
        
        print(f"\n💾 Results saved:")
        print(f"   Detailed: {results_file}")
        print(f"   Summary: {summary_file}")

def main():
    """Main function"""
    print("Headless V2V Distance Validation")
    print("#" * 40)
    
    validator = HeadlessV2VDistanceValidator()
    
    try:
        results = validator.validate_distances(max_samples=10)
        
        if results:
            print("\n🎉 Validation completed successfully!")
        else:
            print("\n❌ Validation failed")
            
    except KeyboardInterrupt:
        print("\n⚠️  Validation interrupted by user")
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
    finally:
        validator.stop_sumo()

if __name__ == "__main__":
    main()
