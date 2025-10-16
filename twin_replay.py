#!/usr/bin/env python3
"""
Digital Twin V2V Replay Orchestrator
Main CLI for running continuous V2V replay simulation
"""

import traci
import yaml
import json
import time
import os
from datetime import datetime
from typing import Dict, List
import argparse

# Import our modules
from utils.dataset import DatasetProcessor
from utils.mapping import GPSSumoMapper
from simulation.replayer import ContinuousReplayer
from validation.metrics import ValidationMetrics
from comm.models import CommunicationCalculator

class DigitalTwinOrchestrator:
    """Main orchestrator for digital twin V2V simulation"""
    
    def __init__(self, config_path: str = "configs/twin_config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.output_dir = self.config.get('output_dir', 'twin_results')
        
        # Initialize components
        self.dataset_processor = DatasetProcessor()
        self.mapper = GPSSumoMapper()
        self.replayer = ContinuousReplayer(
            self.mapper, 
            self.config.get('calibration_factor', 0.607)
        )
        self.validator = ValidationMetrics(
            self.config.get('calibration_factor', 0.607)
        )
        self.comm_calculator = CommunicationCalculator(self.config)
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"🚀 Digital Twin Orchestrator initialized")
        print(f"   Config: {config_path}")
        print(f"   Output: {self.output_dir}")
    
    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            print(f"✅ Configuration loaded from {self.config_path}")
            return config
        except Exception as e:
            print(f"❌ Failed to load config: {e}")
            # Return default config
            return {
                'source_id': 2,
                'destination_id': 4,
                'evaluation_timestamps': 10,
                'min_gap_seconds': 5,
                'simulation_tick': 0.5,
                'calibration_factor': 0.607,
                'carrier_frequency': 5.9e9,
                'tx_power': 23.0,
                'noise_floor': -174.0,
                'bandwidth': 10e6,
                'enable_3gpp_model': True,
                'shadowing_std': 4.0,
                'enable_fading': False
            }
    
    def start_sumo(self) -> bool:
        """Start SUMO simulation"""
        
        try:
            sumo_cmd = ["sumo", "-c", "osm_headless.sumocfg", "--no-step-log"]
            print("🚀 Starting SUMO simulation...")
            traci.start(sumo_cmd)
            time.sleep(2)
            print("✅ SUMO simulation started")
            return True
        except Exception as e:
            print(f"❌ Failed to start SUMO: {e}")
            return False
    
    def stop_sumo(self):
        """Stop SUMO simulation"""
        
        try:
            traci.close()
            print("✅ SUMO simulation stopped")
        except Exception as e:
            print(f"⚠️  Error stopping SUMO: {e}")
    
    def run_digital_twin_simulation(self) -> Dict:
        """Run complete digital twin simulation"""
        
        print("\n" + "="*60)
        print("DIGITAL TWIN V2V REPLAY SIMULATION")
        print("="*60)
        
        try:
            # Step 1: Load and filter dataset
            print("\n📋 Step 1: Loading and filtering dataset...")
            df = self.dataset_processor.load_and_filter(
                self.config['source_id'], 
                self.config['destination_id']
            )
            
            # Step 2: Select evaluation timestamps
            print("\n🎯 Step 2: Selecting evaluation timestamps...")
            evaluation_indices = self.dataset_processor.select_evaluation_timestamps(
                self.config['evaluation_timestamps'],
                self.config['min_gap_seconds']
            )
            
            # Step 3: Get trajectory data
            print("\n📊 Step 3: Preparing trajectory data...")
            timestamps, src_lats, src_lons, dst_lats, dst_lons, distances = \
                self.dataset_processor.get_trajectory_data()
            
            evaluation_distances = distances[evaluation_indices]
            
            print(f"   Total trajectory points: {len(timestamps)}")
            print(f"   Evaluation points: {len(evaluation_indices)}")
            print(f"   Time range: {timestamps[0]:.1f}s - {timestamps[-1]:.1f}s")
            
            # Step 4: Initialize vehicles
            print("\n🚗 Step 4: Initializing vehicles...")
            if not self.replayer.initialize_vehicles(
                self.config['source_id'], 
                self.config['destination_id']
            ):
                return {'success': False, 'error': 'Failed to initialize vehicles'}
            
            # Step 5: Run continuous replay
            print("\n🎬 Step 5: Running continuous replay...")
            replay_results = self.replayer.run_continuous_replay(
                timestamps, src_lats, src_lons, dst_lats, dst_lons,
                evaluation_indices, self.config['simulation_tick']
            )
            
            # Step 6: Calculate communication metrics
            print("\n📡 Step 6: Calculating communication metrics...")
            comm_metrics = self._calculate_communication_metrics(replay_results)
            
            # Step 7: Validate results
            print("\n📊 Step 7: Validating results...")
            distance_metrics = self.validator.calculate_distance_accuracy(
                replay_results['evaluation_data'], evaluation_distances
            )
            
            comm_validation = self.validator.calculate_communication_metrics(
                comm_metrics['snr_values']
            )
            
            # Step 8: Generate outputs
            print("\n💾 Step 8: Generating outputs...")
            self._generate_outputs(replay_results, distance_metrics, 
                                 comm_validation, evaluation_distances)
            
            # Cleanup
            self.replayer.cleanup()
            
            print("\n🎉 Digital twin simulation completed successfully!")
            
            return {
                'success': True,
                'replay_steps': replay_results['total_steps'],
                'evaluation_steps': replay_results['evaluation_steps'],
                'distance_accuracy': distance_metrics.get('mean_error_percentage', 0),
                'communication_success_rate': comm_validation.get('communication_success_rate', 0)
            }
            
        except Exception as e:
            print(f"\n❌ Simulation failed: {e}")
            return {'success': False, 'error': str(e)}
        
        finally:
            self.stop_sumo()
    
    def _calculate_communication_metrics(self, replay_results: Dict) -> Dict:
        """Calculate communication metrics for all replay data"""
        
        snr_values = []
        comm_data = []
        
        for step_data in replay_results['replay_data']:
            if step_data['success']:
                distance = step_data['distance_info']['calibrated_distance']
                
                # Calculate communication metrics
                comm_metrics = self.comm_calculator.calculate_communication_metrics(distance)
                
                snr_values.append(comm_metrics['fspl_snr'])
                comm_data.append({
                    'timestamp': step_data['timestamp'],
                    'sim_time': step_data['sim_time'],
                    'distance': distance,
                    **comm_metrics
                })
        
        return {
            'snr_values': snr_values,
            'comm_data': comm_data
        }
    
    def _generate_outputs(self, replay_results: Dict, distance_metrics: Dict,
                         comm_metrics: Dict, evaluation_distances):
        """Generate output files"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. JSONL per-step data
        if self.config.get('save_per_step_data', True):
            jsonl_file = os.path.join(self.output_dir, f"replay_data_{timestamp}.jsonl")
            with open(jsonl_file, 'w') as f:
                for step_data in replay_results['replay_data']:
                    json.dump(step_data, f)
                    f.write('\n')
            print(f"✅ Per-step data saved: {jsonl_file}")
        
        # 2. CSV evaluation data
        if self.config.get('save_evaluation_data', True):
            csv_file = os.path.join(self.output_dir, f"evaluation_data_{timestamp}.csv")
            self.validator.export_evaluation_csv(
                replay_results['evaluation_data'], 
                evaluation_distances,
                csv_file
            )
        
        # 3. Summary text file
        summary_file = os.path.join(self.output_dir, f"summary_{timestamp}.txt")
        summary_text = self.validator.generate_validation_summary(
            distance_metrics, comm_metrics
        )
        
        with open(summary_file, 'w') as f:
            f.write(summary_text)
        
        print(f"✅ Summary saved: {summary_file}")
        
        # 4. Configuration backup
        config_file = os.path.join(self.output_dir, f"config_{timestamp}.yaml")
        with open(config_file, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
        
        print(f"✅ Configuration saved: {config_file}")

def main():
    """Main CLI function"""
    
    parser = argparse.ArgumentParser(description='Digital Twin V2V Replay Simulation')
    parser.add_argument('--config', '-c', default='configs/twin_config.yaml',
                       help='Configuration file path')
    parser.add_argument('--source-id', type=int, help='Source vehicle ID (overrides config)')
    parser.add_argument('--dest-id', type=int, help='Destination vehicle ID (overrides config)')
    parser.add_argument('--eval-points', type=int, help='Number of evaluation points (overrides config)')
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    orchestrator = DigitalTwinOrchestrator(args.config)
    
    # Override config with command line arguments
    if args.source_id:
        orchestrator.config['source_id'] = args.source_id
    if args.dest_id:
        orchestrator.config['destination_id'] = args.dest_id
    if args.eval_points:
        orchestrator.config['evaluation_timestamps'] = args.eval_points
    
    # Start SUMO
    if orchestrator.start_sumo():
        # Run simulation
        results = orchestrator.run_digital_twin_simulation()
        
        if results['success']:
            print(f"\n📊 Final Results:")
            print(f"   Replay steps: {results['replay_steps']}")
            print(f"   Evaluation steps: {results['evaluation_steps']}")
            print(f"   Distance accuracy: {results['distance_accuracy']:.1f}%")
            print(f"   Communication success: {results['communication_success_rate']:.1f}%")
        else:
            print(f"\n❌ Simulation failed: {results.get('error', 'Unknown error')}")
    else:
        print("\n❌ Failed to start SUMO simulation")

if __name__ == "__main__":
    main()
