@echo off
echo ======================================================================
echo V2V Approach 5: Fine-Tuned Calibration
echo ======================================================================
echo.
echo This approach uses zone-based calibration factors optimized
echo per waypoint region for maximum accuracy.
echo.
echo Features:
echo - Analyze existing errors to find optimal calibration per zone
echo - Zone-based calibration factors:
echo   * Zone 1 (0-49): 0.58
echo   * Zone 2 (50-99): 0.62
echo   * Zone 3 (100-149): 0.61
echo   * Zone 4 (150-199): 0.59
echo - Realistic speed from GPS dataset
echo - Machine learning-based optimization (optional)
echo.
echo Expected improvement: 72-78%% accuracy
echo.
echo Output files:
echo - approach_5_fine_tuned_calib_analysis.csv
echo - approach_5_fine_tuned_calib_summary.json
echo.
echo ======================================================================
echo Starting simulation...
echo ======================================================================
echo.

python v2v_approach_calibrated.py

echo.
echo ======================================================================
echo Simulation completed!
echo ======================================================================
echo.
echo Check the main project folder for output files:
echo - approach_5_fine_tuned_calib_analysis.csv
echo - approach_5_fine_tuned_calib_summary.json
echo.
pause
