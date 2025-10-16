@echo off
echo ======================================================================
echo V2V Approach Comparison Tool
echo ======================================================================
echo.
echo This tool runs all 5 approaches and generates a comprehensive
echo comparison report with statistical analysis and visualizations.
echo.
echo Approaches compared:
echo 1. Baseline 200pts - Extended baseline with 200 waypoints
echo 2. Improved Routing - Enhanced route planning
echo 3. GPS Forcing - Periodic GPS corrections
echo 4. Hybrid - Best of routing + GPS forcing
echo 5. Fine-Tuned Calib - Zone-based calibration
echo.
echo Output files:
echo - comparison_report.csv
echo - comparison_plots.png
echo.
echo ======================================================================
echo Starting comparison...
echo ======================================================================
echo.

python compare_all_approaches.py

echo.
echo ======================================================================
echo Comparison completed!
echo ======================================================================
echo.
echo Check the main project folder for output files:
echo - comparison_report.csv
echo - comparison_plots.png
echo.
echo The comparison will show:
echo - Mean accuracy for each approach
echo - Error metrics (RMSE, MAE)
echo - Waypoint distribution analysis
echo - Speed accuracy comparison
echo - Winner recommendation
echo.
pause
