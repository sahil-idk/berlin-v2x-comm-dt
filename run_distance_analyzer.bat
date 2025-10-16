@echo off
echo ========================================
echo    Distance Accuracy Analyzer
echo ========================================
echo.
echo This tool provides comprehensive analysis of:
echo - Distance accuracy between actual and simulated vehicles
echo - Statistical metrics (MAE, RMSE, correlation)
echo - Visualizations and charts
echo - Best/worst performing waypoints
echo - Overall assessment and recommendations
echo.
echo Starting analyzer...
echo.

python distance_accuracy_analyzer.py

echo.
echo ========================================
echo Analysis completed!
echo.
echo Check the generated visualizations and
echo analysis results above.
echo ========================================
pause
