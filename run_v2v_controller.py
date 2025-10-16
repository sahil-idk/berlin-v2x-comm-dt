#!/usr/bin/env python3
"""
Simple launcher for the V2V Simulation Controller
"""

import sys
import os

def main():
    """Launch the simulation controller"""
    try:
        print("Starting V2V Sumulation Controller...")
        from tkinter_simulation_controller import TkinterSimulationController
        
        # Create and run the controller
        controller = TkinterSimulationController()
        controller.run()
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure all required packages are installed:")
        print("- tkinter (usually comes with Python)")
        print("- pandas")
        print("- numpy") 
        print("- SUMO and TraCI")
        sys.exit(1)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
