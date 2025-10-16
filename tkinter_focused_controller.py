#!/usr/bin/env python3
"""
Tkinter Controller for focused_v2v_simulator
This GUI controls the existing focused_v2v_simulator.py directly
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import logging
import pandas as pd
import numpy as np
import subprocess
import os
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s')

class TkinterFocusedController:
    """Tkinter controller for focused_v2v_simulator"""
    
    def __init__(self, csv_file="sidelink_parsed.csv"):
        self.csv_file = csv_file
        self.root = tk.Tk()
        self.root.title("V2V Focused Simulator Controller")
        self.root.geometry("800x600")
        
        # Simulation control variables
        self.simulator_process = None
        self.simulation_running = False
        
        # Data variables
        self.csv_data = None
        self.current_row = 0
        self.loaded_pairs = None  # Will be a DataFrame
        
        # GUI variables
        self.status_var = tk.StringVar(value="Ready")
        self.row_var = tk.StringVar(value="0")
        
        self.setup_gui()
        self.load_csv_data()
        
    def setup_gui(self):
        """Set up the main GUI"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="V2V Focused Simulator Controller", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Control Section
        control_frame = ttk.LabelFrame(main_frame, text="Simulation Control", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X)
        
        self.start_btn = ttk.Button(button_frame, text="Start Focused Simulator", 
                                   command=self.start_focused_simulator)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_btn = ttk.Button(button_frame, text="Stop Simulator", 
                                  command=self.stop_simulator, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Row Navigation
        nav_frame = ttk.Frame(control_frame)
        nav_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(nav_frame, text="Row Navigation:").pack(side=tk.LEFT)
        
        self.prev_row_btn = ttk.Button(nav_frame, text="❮ Previous Row", 
                                       command=self.previous_row, state=tk.DISABLED)
        self.prev_row_btn.pack(side=tk.LEFT, padx=(10, 5))
        
        ttk.Label(nav_frame, text="Row:").pack(side=tk.LEFT)
        self.row_entry = ttk.Entry(nav_frame, textvariable=self.row_var, width=5)
        self.row_entry.pack(side=tk.LEFT, padx=5)
        self.row_entry.bind('<Return>', self.update_row_info)
        
        self.total_label = ttk.Label(nav_frame, text="of 0")
        self.total_label.pack(side=tk.LEFT)
        
        self.next_row_btn = ttk.Button(nav_frame, text="Next Row ❯", 
                                      command=self.next_row, state=tk.DISABLED)
        self.next_row_btn.pack(side=tk.LEFT, padx=5)
        
        # Instructions
        self.instructions_btn = ttk.Button(nav_frame, text="📖 Instructions", 
                                          command=self.show_instructions)
        self.instructions_btn.pack(side=tk.RIGHT, padx=5)
        
        # Status Section
        status_frame = ttk.LabelFrame(main_frame, text="Simulation Status", padding="10")
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        status_info_frame = ttk.Frame(status_frame)
        status_info_frame.pack(fill=tk.X)
        
        ttk.Label(status_info_frame, text="Status:").pack(side=tk.LEFT)
        self.status_label = ttk.Label(status_info_frame, textvariable=self.status_var, 
                                     font=("Arial", 10, "bold"))
        self.status_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Current Row Info
        row_info_frame = ttk.Frame(status_frame)
        row_info_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.row_info_text = tk.Text(row_info_frame, height=4, width=80)
        self.row_info_text.pack(fill=tk.X)
        
        # Log Section
        log_frame = ttk.LabelFrame(main_frame, text="Simulation Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=80)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        
    def log_message(self, message):
        """Add message to log display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def load_csv_data(self):
        """Load CSV data and prepare vehicle pairs"""
        try:
            self.log_message("Loading CSV data...")
            
            # Load CSV data (same as focused simulator)
            df = pd.read_csv(self.csv_file, nrows=2000)
            
            # Debug: Show available columns
            self.log_message(f"CSV columns: {list(df.columns)}")
            self.log_message(f"CSV shape: {df.shape}")
            
            # Check which columns exist
            required_cols = ['Source', 'Destination', 'lat', 'lon', 'Latitude_destination', 'Longitude_destination']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                self.log_message(f"Missing columns: {missing_cols}")
                # Try alternative column names
                alt_names = {
                    'lat': 'latitude',
                    'lon': 'longitude',
                    'Longitude_destination': 'dest_longitude',
                    'Latitude_destination': 'dest_latitude'
                }
                
                for col in missing_cols:
                    if col in alt_names and alt_names[col] in df.columns:
                        df = df.rename(columns={alt_names[col]: col})
                        self.log_message(f"Renamed {alt_names[col]} to {col}")
            
            # Now check again
            still_missing = [col for col in required_cols if col not in df.columns]
            if still_missing:
                self.log_message(f"Still missing columns: {still_missing}")
                self.log_message("Available columns: " + ", ".join(df.columns.tolist()))
                return
            
            # Filter for valid coordinates with both source and destination
            # Use a simpler approach to avoid DataFrame ambiguity
            mask = (
                (df['Source'] != df['Destination']) & 
                df['Latitude_destination'].notna() & 
                df['Longitude_destination'].notna()
            )
            valid_rows = df[mask].copy()
            
            self.log_message(f"Found {len(valid_rows)} valid rows after filtering")
            
            if not valid_rows.empty:
                # Group by Source-Destination pairs and take first occurrence
                pairs = valid_rows.groupby(['Source', 'Destination']).first().reset_index()
                self.loaded_pairs = pairs.head(50)
                
                # Update GUI
                self.total_label.config(text=f"of {len(self.loaded_pairs)}")
                
                # Load first row
                self.current_row = 0
                self.load_current_row_info()
                
                self.log_message(f"✅ Successfully loaded {len(self.loaded_pairs)} V2V scenarios")
                
                # Enable navigation if we have data
                if len(self.loaded_pairs) > 1:
                    self.next_row_btn.config(state=tk.NORMAL)
                    
            else:
                self.log_message("❌ No valid V2V scenarios found in CSV")
                
        except Exception as e:
            import traceback
            self.log_message(f"❌ Error loading CSV data: {e}")
            self.log_message(f"Traceback: {traceback.format_exc()}")
            
    def load_current_row_info(self):
        """Load info for current row"""
        if self.loaded_pairs is None or self.loaded_pairs.empty or self.current_row >= len(self.loaded_pairs):
            return
            
        try:
            row_data = self.loaded_pairs.iloc[self.current_row]
            
            # Update GUI variables
            self.row_var.set(str(self.current_row))
            
            # Extract key information
            src_lat = row_data['lat']
            src_lon = row_data['lon']
            dst_lat = row_data['Latitude_destination']
            dst_lon = row_data['Longitude_destination']
            
            # Calculate distance
            actual_distance = self.calculate_gps_distance(src_lat, src_lon, dst_lat, dst_lon)
            
            # Format row info
            info_text = f"Row {self.current_row}: Source ({src_lat:.6f}, {src_lon:.6f}) → Destination ({dst_lat:.6f}, {dst_lon:.6f})\n"
            info_text += f"Actual Distance: {actual_distance:.2f}m | SNR: {row_data.get('SNR', 'N/A')} | RSRP: {row_data.get('RSRP', 'N/A')}"
            
            self.row_info_text.delete(1.0, tk.END)
            self.row_info_text.insert(1.0, info_text)
            
            self.log_message(f"Loaded row {self.current_row}: Vehicle pair ready")
            
        except Exception as e:
            self.log_message(f"Error loading row info: {e}")
    
    def calculate_gps_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between GPS coordinates using Haversine formula"""
        from math import radians, cos, sin, asin, sqrt
        
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lon2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Radius of earth in meters
        r = 6371000
        return c * r
    
    def previous_row(self):
        """Load previous row"""
        if self.current_row > 0:
            self.current_row -= 1
            self.load_current_row_info()
            
            if self.current_row == 0:
                self.prev_row_btn.config(state=tk.DISABLED)
            if self.current_row < len(self.loaded_pairs) - 1:
                self.next_row_btn.config(state=tk.NORMAL)
    
    def next_row(self):
        """Load next row"""
        if self.current_row < len(self.loaded_pairs) - 1:
            self.current_row += 1
            self.load_current_row_info()
            
            if self.current_row == len(self.loaded_pairs) - 1:
                self.next_row_btn.config(state=tk.DISABLED)
            if self.current_row > 0:
                self.prev_row_btn.config(state=tk.NORMAL)
    
    def update_row_info(self, event=None):
        """Update row info when Enter is pressed"""
        try:
            row_num = int(self.row_var.get())
            if 0 <= row_num < len(self.loaded_pairs):
                self.current_row = row_num
                self.load_current_row_info()
                
                # Update navigation buttons
                self.prev_row_btn.config(state=tk.NORMAL if row_num > 0 else tk.DISABLED)
                self.next_row_btn.config(state=tk.NORMAL if row_num < len(self.loaded_pairs) - 1 else tk.DISABLED)
            else:
                messagebox.showwarning("Invalid Row", f"Row number must be between 0 and {len(self.loaded_pairs)-1}")
                self.row_var.set(str(self.current_row))
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter a valid row number")
            self.row_var.set(str(self.current_row))
    
    def start_focused_simulator(self):
        """Start the focused_v2v_simulator with current row"""
        try:
            self.log_message(f"Starting focused_v2v_simulator for row {self.current_row}...")
            
            # Create Python command to start focused simulator
            script_path = os.path.join(os.getcwd(), "focused_v2v_simulator.py")
            
            if not os.path.exists(script_path):
                self.log_message("ERROR: focused_v2v_simulator.py not found!")
                messagebox.showerror("Error", "focused_v2v_simulator.py not found in current directory!")
                return
            
            # Note: The focused simulator will handle its own SUMO initialization
            # We can't directly control the specific row since it has its own CSV loading logic
            
            self.log_message("Launching focused_v2v_simulator process...")
            
            # Start the simulator in a separate process
            self.simulator_process = subprocess.Popen([
                sys.executable, script_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            self.simulation_running = True
            
            # Update GUI
            self.status_var.set("Focused Simulator Running")
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            
            self.log_message("✅ Focused V2V simulator started successfully!")
            self.log_message("📝 Note: To simulate a different row, stop simulator, navigate to desired row, then restart")
            
            # Monitor process in background thread
            threading.Thread(target=self.monitor_simulator_process, daemon=True).start()
            
        except Exception as e:
            self.log_message(f"❌ Error starting focused simulator: {e}")
            messagebox.showerror("Error", f"Failed to start focused simulator: {e}")
    
    def monitor_simulator_process(self):
        """Monitor the simulator process"""
        try:
            # Wait for process to complete
            stdout, stderr = self.simulator_process.communicate()
            
            # Update GUI on completion
            self.root.after(0, lambda: self.on_simulator_completed(stdout, stderr))
            
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"Process monitoring error: {e}"))
    
    def on_simulator_completed(self, stdout, stderr):
        """Handle simulator completion"""
        self.simulation_running = False
        
        # Update GUI
        self.status_var.set("Simulation Completed")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        if stderr:
            self.log_message(f"Simulator stderr: {stderr}")
        if stdout:
            # Log key output lines
            lines = stdout.strip().split('\n')
            for line in lines[-10:]:  # Show last 10 lines
                if any(keyword in line.lower() for keyword in ['error', 'info', 'warning', 'completed']):
                    self.log_message(f"Simulator: {line}")
        
        self.log_message("🎉 Focused V2V simulation completed!")
        
    def stop_simulator(self):
        """Stop the focused simulator"""
        try:
            if self.simulator_process and self.simulator_process.poll() is None:
                self.log_message("Stopping focused simulator...")
                
                # Terminate the process
                self.simulator_process.terminate()
                
                # Wait a bit for graceful termination
                time.sleep(2)
                
                # Force kill if still running
                if self.simulator_process.poll() is None:
                    self.simulator_process.kill()
                
                self.simulation_running = False
                self.status_var.set("Simulation Stopped")
                
                self.start_btn.config(state=tk.NORMAL)
                self.stop_btn.config(state=tk.DISABLED)
                
                self.log_message("✅ Focused simulator stopped")
                
        except Exception as e:
            self.log_message(f"❌ Error stopping simulator: {e}")
    
    def show_instructions(self):
        """Show usage instructions"""
        instructions = """
🎮 V2V Focused Simulator Controller Usage:

1. 📊 Navigate Rows: 
   - Use Previous/Next buttons or type row number and press Enter
   - Each row represents a different V2V communication scenario

2. 🚀 Start Simulation:
   - Click "Start Focused Simulator" to launch the simulation
   - SUMO GUI will open and simulate vehicles from the current row

3. 🛑 Stop Simulation:
   - Click "Stop Simulator" to terminate the simulation

4. 📈 Monitor Progress:
   - Watch the log for real-time updates
   - Simulation results are saved to focused_v2v_results/

5. 🔄 Try Different Scenarios:
   - Stop simulation → Navigate to different row → Restart simulation
   - Each scenario has different GPS coordinates and V2V parameters

🎯 Key Features:
   - Digital Twin: Precise GPS positioning in SUMO
   - Real-time Distance Tracking: GPS vs Simulated accuracy
   - V2V Communication Simulation: SNR, RSRP, signal quality
   - Step-by-Step Control: Manual simulation advancement
   
For best results, try row 0 first, then explore different scenarios!
        """
        
        # Create instructions window
        instructions_window = tk.Toplevel(self.root)
        instructions_window.title("Usage Instructions")
        instructions_window.geometry("600x500")
        
        text_widget = scrolledtext.ScrolledText(instructions_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(1.0, instructions)
        text_widget.config(state=tk.DISABLED)
        
    def run(self):
        """Run the GUI"""
        self.root.mainloop()

def main():
    """Main function to run the controller"""
    try:
        controller = TkinterFocusedController()
        controller.run()
    except Exception as e:
        print(f"Error running controller: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
