@echo off
echo ======================================================================
echo V2V Simulation with Realistic Speeds
echo ======================================================================
echo.
echo This simulation uses ACTUAL vehicle speeds from GPS dataset!
echo.
echo Output Files (saved to main project folder):
echo   - realistic_speed_waypoint_analysis.csv
echo   - realistic_speed_simulation_summary.json
echo.
echo Features:
echo   [x] Distance accuracy per waypoint
echo   [x] Speed accuracy per waypoint
echo   [x] Overall accuracy metrics
echo   [x] Comparison of actual vs simulated values
echo.
echo ======================================================================
echo.
python v2v_realistic_speed_simulation.py
echo.
echo ======================================================================
echo Check output files in: C:\Users\sahil\Sumo\berlin_v2x\
echo ======================================================================
pause

