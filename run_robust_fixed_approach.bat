@echo off
echo ========================================
echo    V2V Robust Fixed Simulation Approach
echo ========================================
echo.
echo This approach focuses on fixing core issues:
echo - Robust edge mapping with fallback strategies
echo - Vehicle-specific routes to prevent collisions
echo - Departure time offset (5s delay)
echo - Route validation and connectivity checks
echo - Comprehensive distance accuracy analysis
echo.
echo Starting simulation...
echo.

python v2v_robust_fixed_approach.py

echo.
echo ========================================
echo Simulation completed!
echo.
echo Output files saved to main project folder:
echo - robust_fixed_distance_accuracy_analysis.csv
echo - robust_fixed_simulation_summary.json
echo ========================================
pause
