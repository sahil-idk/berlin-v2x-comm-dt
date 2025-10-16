@echo off
echo ================================================================================
echo V2V SIMULATION - COMBINED OPTIMAL STRATEGY
echo ================================================================================
echo.
echo 🏆 This is the COMBINED OPTIMAL strategy that combines all 5 improvements:
echo    1. Multi-Zone Distance Calibration (5 zones)
echo    2. Velocity-Based Adjustment (slow/normal/fast)
echo    3. Statistical Outlier Detection (z-score threshold)
echo    4. Adaptive Learning (self-adjusting calibration)
echo    5. Intelligent Combination (weighted: Zone 50%%, Velocity 30%%, Adaptive 20%%)
echo.
echo 🎯 Target: 80%%+ accuracy (Baseline: 66.52%%)
echo.
echo Features:
echo    ✅ SUMO-GUI with visual display
echo    ✅ Tkinter control panel with real-time status
echo    ✅ Configurable waypoints (5-200)
echo    ✅ Realistic speeds from GPS dataset
echo    ✅ Toggle Combined Optimal calibration on/off
echo    ✅ Comprehensive accuracy analysis
echo.
echo Output files:
echo    📄 combined_optimal_results.csv (per-waypoint details)
echo    📄 combined_optimal_summary.json (overall metrics)
echo.
echo ================================================================================
pause

python v2v_combined_optimal.py

echo.
echo ================================================================================
echo Simulation complete! Check the generated files for results.
echo ================================================================================
pause

