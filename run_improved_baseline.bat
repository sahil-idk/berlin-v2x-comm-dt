@echo off
echo ========================================
echo   V2V Improved Baseline Simulation
echo ========================================
echo.
echo BASELINE: 66.52%% accuracy
echo TARGET: 80%%+ accuracy
echo.
echo IMPROVEMENTS:
echo - Multi-zone adaptive calibration
echo - Distance + velocity based factors
echo - Statistical outlier detection
echo - Dynamic calibration tuning
echo - Proven route stability
echo.
echo Starting simulation...
echo.

python v2v_improved_baseline.py

echo.
echo ========================================
echo Simulation completed!
echo.
echo Output files:
echo - improved_baseline_distance_analysis.csv
echo - improved_baseline_summary.json
echo ========================================
pause
