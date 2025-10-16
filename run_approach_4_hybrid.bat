@echo off
echo ======================================================================
echo V2V Approach 4: Hybrid Route + GPS Correction
echo ======================================================================
echo.
echo This approach combines the best of improved routing and GPS forcing
echo for optimal accuracy and simulation stability.
echo.
echo Features:
echo - Improved routing (every 5th point, all edges, extensions)
echo - Selective GPS forcing only when deviation >30m
echo - Dynamic calibration based on waypoint region
echo - Realistic speed from GPS dataset
echo - Calibration factor: 0.607 (with zone-based adjustments)
echo.
echo Expected improvement: 78-85%% accuracy (BEST APPROACH)
echo.
echo Output files:
echo - approach_4_hybrid_analysis.csv
echo - approach_4_hybrid_summary.json
echo.
echo ======================================================================
echo Starting simulation...
echo ======================================================================
echo.

python v2v_approach_hybrid.py

echo.
echo ======================================================================
echo Simulation completed!
echo ======================================================================
echo.
echo Check the main project folder for output files:
echo - approach_4_hybrid_analysis.csv
echo - approach_4_hybrid_summary.json
echo.
pause
