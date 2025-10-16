@echo off
echo ======================================================================
echo V2V Approach 1: Extended Baseline (200 points)
echo ======================================================================
echo.
echo This approach extends the baseline to support 200 waypoints
echo with increased simulation steps for comprehensive analysis.
echo.
echo Features:
echo - GUI slider supports 1-200 waypoints
echo - Default: 50 waypoints (increased from 30)
echo - Simulation steps: 6000 (increased from 3000)
echo - Realistic speed from GPS dataset
echo - Calibration factor: 0.607
echo.
echo Output files:
echo - realistic_speed_waypoint_analysis.csv
echo - realistic_speed_simulation_summary.json
echo.
echo ======================================================================
echo Starting simulation...
echo ======================================================================
echo.

python v2v_realistic_speed_simulation.py

echo.
echo ======================================================================
echo Simulation completed!
echo ======================================================================
echo.
echo Check the main project folder for output files:
echo - realistic_speed_waypoint_analysis.csv
echo - realistic_speed_simulation_summary.json
echo.
pause
