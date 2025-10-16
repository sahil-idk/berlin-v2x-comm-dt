@echo off
echo ========================================
echo    V2V Lane-Based Simulation Approach
echo ========================================
echo.
echo This approach focuses on lane-based positioning
echo to prevent vehicles from going off-road.
echo.
echo Key features:
echo - GPS coordinates mapped to specific lanes
echo - Lane-based vehicle positioning
echo - Route validation for connectivity
echo - Pure route-based movement (no moveToXY)
echo - Comprehensive distance accuracy analysis
echo.
echo Starting simulation...
echo.

python v2v_lane_based_approach.py

echo.
echo ========================================
echo Simulation completed!
echo.
echo Output files saved to main project folder:
echo - lane_based_distance_accuracy_analysis.csv
echo - lane_based_simulation_summary.json
echo ========================================
pause
