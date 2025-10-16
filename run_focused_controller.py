#!/usr/bin/env python3
"""
Simple launcher for the V2V Focused Simulator Controller
"""

import sys
import os

def main():
    """Launch the focused simulator controller"""
    try:
        print("🚀 Starting V2V Focused Simulator Controller...")
        print("📝 This GUI controls the focused_v2v_simulator.py")
        print("🎮 Features: Row navigation, simulation control, real-time monitoring")
        print("-" * 60)
        
        from tkinter_focused_controller import TkinterFocusedController
        
        # Create and run the controller
        controller = TkinterFocusedController()
        controller.run()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all required packages are installed:")
        print("- tkinter (usually comes with Python)")
        print("- pandas")
        print("- numpy") 
        print("- focused_v2v_simulator.py exists in current directory")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
