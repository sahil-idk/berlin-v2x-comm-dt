@echo off
echo ======================================================================
echo V2V Approach 3: GPS Waypoint Forcing (moveToXY)
echo ======================================================================
echo.
echo This approach uses periodic GPS corrections with moveToXY
echo for tighter GPS adherence and better waypoint following.
echo.
echo Features:
echo - Periodic GPS corrections every 10 simulation steps
echo - moveToXY with keepRoute=2 and matchThreshold=500
echo - Waypoint proximity detection (advance when within 20m)
echo - Realistic speed from GPS dataset
echo - Calibration factor: 0.607
echo.
echo Expected improvement: 75-80%% accuracy
echo.
echo Output files:
echo - approach_3_gps_forcing_analysis.csv
echo - approach_3_gps_forcing_summary.json
echo.
echo ======================================================================
echo Starting simulation...
echo ======================================================================
echo.

python v2v_approach_gps_forcing.py

echo.
echo ======================================================================
echo Simulation completed!
echo ======================================================================
echo.
echo Check the main project folder for output files:
echo - approach_3_gps_forcing_analysis.csv
echo - approach_3_gps_forcing_summary.json
echo.
pause
