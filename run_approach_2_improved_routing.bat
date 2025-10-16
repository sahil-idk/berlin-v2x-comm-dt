@echo off
echo ======================================================================
echo V2V Approach 2: Improved Route Planning
echo ======================================================================
echo.
echo This approach enhances route planning with better waypoint sampling
echo and edge handling for improved trajectory following.
echo.
echo Features:
echo - Sample every 5th point instead of current sampling strategy
echo - Use all intermediate edges in Dijkstra path (no uniqueness check)
echo - Add edge extensions at start/end for smoother entry/exit
echo - Realistic speed from GPS dataset
echo - Calibration factor: 0.607
echo.
echo Expected improvement: 70-75%% accuracy
echo.
echo Output files:
echo - approach_2_improved_routing_analysis.csv
echo - approach_2_improved_routing_summary.json
echo.
echo ======================================================================
echo Starting simulation...
echo ======================================================================
echo.

python v2v_approach_improved_routing.py

echo.
echo ======================================================================
echo Simulation completed!
echo ======================================================================
echo.
echo Check the main project folder for output files:
echo - approach_2_improved_routing_analysis.csv
echo - approach_2_improved_routing_summary.json
echo.
pause
