#!/usr/bin/env python3
"""
Communication models for V2V digital twin simulation
"""

import math
import numpy as np
from typing import Dict, Tuple, Optional
import random

class FSPLModel:
    """Free Space Path Loss communication model"""
    
    def __init__(self, frequency: float = 5.9e9, tx_power: float = 23.0, 
                 noise_floor: float = -174.0, bandwidth: float = 10e6):
        """
        Initialize FSPL model
        
        Args:
            frequency: Carrier frequency in Hz (default: 5.9 GHz)
            tx_power: Transmit power in dBm (default: 23 dBm)
            noise_floor: Noise floor in dBm/Hz (default: -174 dBm/Hz)
            bandwidth: Bandwidth in Hz (default: 10 MHz)
        """
        self.frequency = frequency
        self.tx_power = tx_power
        self.noise_floor = noise_floor
        self.bandwidth = bandwidth
        
        # Calculate noise power
        self.noise_power = noise_floor + 10 * math.log10(bandwidth)
        
        print(f"📡 FSPL Model initialized:")
        print(f"   Frequency: {frequency/1e9:.1f} GHz")
        print(f"   Tx Power: {tx_power} dBm")
        print(f"   Noise Power: {self.noise_power:.1f} dBm")
    
    def calculate_path_loss(self, distance: float) -> float:
        """Calculate free space path loss"""
        
        if distance <= 0:
            return 0
        
        # Free space path loss formula: 20*log10(4*pi*d/lambda)
        # lambda = c/f
        c = 3e8  # Speed of light
        wavelength = c / self.frequency
        
        path_loss = 20 * math.log10(4 * math.pi * distance / wavelength)
        
        return path_loss
    
    def calculate_snr(self, distance: float) -> float:
        """Calculate Signal-to-Noise Ratio"""
        
        path_loss = self.calculate_path_loss(distance)
        received_power = self.tx_power - path_loss
        
        snr = received_power - self.noise_power
        
        return snr
    
    def calculate_rsrp(self, distance: float) -> float:
        """Calculate Reference Signal Received Power"""
        
        path_loss = self.calculate_path_loss(distance)
        rsrp = self.tx_power - path_loss
        
        return rsrp
    
    def calculate_rssi(self, distance: float) -> float:
        """Calculate Received Signal Strength Indicator"""
        
        rsrp = self.calculate_rsrp(distance)
        # RSSI is typically 5-10 dB higher than RSRP
        rssi = rsrp + 5
        
        return rssi

class ThreeGPPUrbanMacroModel:
    """3GPP Urban Macro communication model"""
    
    def __init__(self, frequency: float = 5.9e9, tx_power: float = 23.0,
                 noise_floor: float = -174.0, bandwidth: float = 10e6,
                 shadowing_std: float = 4.0, enable_fading: bool = False):
        """
        Initialize 3GPP Urban Macro model
        
        Args:
            frequency: Carrier frequency in Hz
            tx_power: Transmit power in dBm
            noise_floor: Noise floor in dBm/Hz
            bandwidth: Bandwidth in Hz
            shadowing_std: Log-normal shadowing standard deviation in dB
            enable_fading: Enable small-scale fading
        """
        self.frequency = frequency
        self.tx_power = tx_power
        self.noise_floor = noise_floor
        self.bandwidth = bandwidth
        self.shadowing_std = shadowing_std
        self.enable_fading = enable_fading
        
        # Calculate noise power
        self.noise_power = noise_floor + 10 * math.log10(bandwidth)
        
        print(f"📡 3GPP Urban Macro Model initialized:")
        print(f"   Frequency: {frequency/1e9:.1f} GHz")
        print(f"   Shadowing std: {shadowing_std} dB")
        print(f"   Fading enabled: {enable_fading}")
    
    def determine_los_nlos(self, distance: float, los_probability: float = 0.5) -> bool:
        """
        Determine Line-of-Sight (LOS) or Non-Line-of-Sight (NLOS)
        
        Args:
            distance: Distance in meters
            los_probability: Probability of LOS (default: 0.5)
        
        Returns:
            True if LOS, False if NLOS
        """
        # Simple heuristic: closer distances more likely to be LOS
        # This could be enhanced with building/obstacle data
        distance_factor = min(1.0, max(0.0, 1.0 - distance / 1000.0))
        adjusted_probability = los_probability * distance_factor
        
        return random.random() < adjusted_probability
    
    def calculate_path_loss_3gpp(self, distance: float, is_los: bool = True) -> float:
        """Calculate 3GPP Urban Macro path loss"""
        
        if distance <= 0:
            return 0
        
        # 3GPP TR 38.901 Urban Macro model
        # Frequency in GHz
        freq_ghz = self.frequency / 1e9
        
        if is_los:
            # LOS path loss
            if distance <= 10:
                path_loss = 32.4 + 21 * math.log10(distance) + 20 * math.log10(freq_ghz)
            else:
                path_loss = 32.4 + 21 * math.log10(distance) + 20 * math.log10(freq_ghz)
        else:
            # NLOS path loss
            path_loss = 35.3 * math.log10(distance) + 22.4 + 21.3 * math.log10(freq_ghz)
        
        return path_loss
    
    def add_shadowing(self, path_loss: float) -> float:
        """Add log-normal shadowing"""
        
        shadowing = np.random.normal(0, self.shadowing_std)
        return path_loss + shadowing
    
    def add_fading(self, received_power: float) -> float:
        """Add small-scale fading (Rayleigh)"""
        
        if not self.enable_fading:
            return received_power
        
        # Rayleigh fading: multiply by exponential random variable
        fading_factor = np.random.exponential(1.0)
        faded_power = received_power + 10 * math.log10(fading_factor)
        
        return faded_power
    
    def calculate_snr(self, distance: float, los_probability: float = 0.5) -> Dict[str, float]:
        """Calculate SNR with 3GPP model"""
        
        # Determine LOS/NLOS
        is_los = self.determine_los_nlos(distance, los_probability)
        
        # Calculate path loss
        path_loss = self.calculate_path_loss_3gpp(distance, is_los)
        
        # Add shadowing
        path_loss_with_shadowing = self.add_shadowing(path_loss)
        
        # Calculate received power
        received_power = self.tx_power - path_loss_with_shadowing
        
        # Add fading if enabled
        received_power_with_fading = self.add_fading(received_power)
        
        # Calculate SNR
        snr = received_power_with_fading - self.noise_power
        
        return {
            'snr': snr,
            'rsrp': received_power_with_fading,
            'rssi': received_power_with_fading + 5,
            'path_loss': path_loss_with_shadowing,
            'is_los': is_los,
            'shadowing': path_loss_with_shadowing - path_loss,
            'fading': received_power_with_fading - received_power if self.enable_fading else 0
        }

class CommunicationCalculator:
    """Main communication calculator combining both models"""
    
    def __init__(self, config: Dict):
        """Initialize with configuration"""
        
        self.config = config
        
        # Initialize FSPL model
        self.fspl_model = FSPLModel(
            frequency=config.get('carrier_frequency', 5.9e9),
            tx_power=config.get('tx_power', 23.0),
            noise_floor=config.get('noise_floor', -174.0),
            bandwidth=config.get('bandwidth', 10e6)
        )
        
        # Initialize 3GPP model if enabled
        if config.get('enable_3gpp_model', False):
            self.gpp_model = ThreeGPPUrbanMacroModel(
                frequency=config.get('carrier_frequency', 5.9e9),
                tx_power=config.get('tx_power', 23.0),
                noise_floor=config.get('noise_floor', -174.0),
                bandwidth=config.get('bandwidth', 10e6),
                shadowing_std=config.get('shadowing_std', 4.0),
                enable_fading=config.get('enable_fading', False)
            )
        else:
            self.gpp_model = None
    
    def calculate_communication_metrics(self, distance: float) -> Dict[str, float]:
        """Calculate communication metrics for given distance"""
        
        # Calculate FSPL metrics
        fspl_snr = self.fspl_model.calculate_snr(distance)
        fspl_rsrp = self.fspl_model.calculate_rsrp(distance)
        fspl_rssi = self.fspl_model.calculate_rssi(distance)
        
        result = {
            'distance': distance,
            'fspl_snr': fspl_snr,
            'fspl_rsrp': fspl_rsrp,
            'fspl_rssi': fspl_rssi
        }
        
        # Calculate 3GPP metrics if enabled
        if self.gpp_model:
            gpp_metrics = self.gpp_model.calculate_snr(distance)
            result.update({
                'gpp_snr': gpp_metrics['snr'],
                'gpp_rsrp': gpp_metrics['rsrp'],
                'gpp_rssi': gpp_metrics['rssi'],
                'gpp_path_loss': gpp_metrics['path_loss'],
                'gpp_is_los': gpp_metrics['is_los'],
                'gpp_shadowing': gpp_metrics['shadowing'],
                'gpp_fading': gpp_metrics['fading']
            })
        
        return result
