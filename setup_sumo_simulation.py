#!/usr/bin/env python3
"""
Setup script for SUMO TraCI simulation with PC2 data
"""

import os
import subprocess
import sys

def check_sumo_installation():
    """Check if SUMO is installed and accessible"""
    print("Checking SUMO installation...")
    
    try:
        result = subprocess.run(['sumo', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ SUMO found: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    try:
        result = subprocess.run(['sumo-gui', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ SUMO-GUI found: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ SUMO not found!")
    print("Please install SUMO from: https://sumo.dlr.de/docs/Downloads.php")
    print("Make sure to add SUMO to your PATH environment variable.")
    return False

def check_python_packages():
    """Check if required Python packages are installed"""
    print("\nChecking Python packages...")
    
    required_packages = ['pandas', 'numpy', 'traci']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} found")
        except ImportError:
            print(f"❌ {package} not found")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        
        for package in missing_packages:
            if package == 'traci':
                # TraCI comes with SUMO installation
                print("Note: traci package comes with SUMO installation")
                continue
            
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', package], check=True)
                print(f"✅ {package} installed successfully")
            except subprocess.CalledProcessError:
                print(f"❌ Failed to install {package}")
                return False
    
    return True

def create_required_files():
    """Create all required files for the simulation"""
    print("\nCreating required files...")
    
    # Check if PC2 data exists
    if not os.path.exists('pc2_parsed.csv'):
        print("❌ pc2_parsed.csv not found!")
        print("Please run the parquet to CSV conversion first.")
        return False
    
    # Create simple network
    if not os.path.exists('berlin_network.net.xml'):
        print("Creating simple Berlin network...")
        from create_simple_berlin_network import create_simple_network
        create_simple_network()
    
    # Check if all files exist
    required_files = [
        'berlin_simulation.sumocfg',
        'berlin_routes.rou.xml',
        'berlin_additional.add.xml',
        'berlin_network.net.xml',
        'pc2_parsed.csv'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} missing")
            return False
    
    return True

def run_simulation():
    """Run the SUMO simulation"""
    print("\n" + "="*50)
    print("STARTING SUMO TRACI SIMULATION")
    print("="*50)
    
    try:
        from simple_sumo_traci import main
        return main()
    except Exception as e:
        print(f"Error running simulation: {e}")
        return False

def main():
    """Main setup function"""
    print("=== SUMO TraCI Simulation Setup ===\n")
    
    # Check SUMO installation
    if not check_sumo_installation():
        return False
    
    # Check Python packages
    if not check_python_packages():
        return False
    
    # Create required files
    if not create_required_files():
        return False
    
    print("\n✅ Setup completed successfully!")
    print("\nFiles created:")
    print("- berlin_network.net.xml (SUMO network)")
    print("- berlin_simulation.sumocfg (SUMO configuration)")
    print("- berlin_routes.rou.xml (vehicle routes)")
    print("- berlin_additional.add.xml (additional elements)")
    print("- simple_sumo_traci.py (TraCI simulation script)")
    
    print("\nTo run the simulation:")
    print("python simple_sumo_traci.py")
    
    # Ask user if they want to run simulation now
    response = input("\nDo you want to run the simulation now? (y/n): ").lower().strip()
    if response in ['y', 'yes']:
        return run_simulation()
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Setup completed successfully!")
    else:
        print("\n❌ Setup failed!")
