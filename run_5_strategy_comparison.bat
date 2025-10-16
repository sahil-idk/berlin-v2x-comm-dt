@echo off
echo ================================================================================
echo V2V 5-STRATEGY ACCURACY COMPARISON
echo ================================================================================
echo.
echo This will run 5 different calibration strategies and compare results:
echo   1. Multi-Zone Distance-Based Calibration
echo   2. Velocity-Based Adjustment
echo   3. Statistical Outlier Detection
echo   4. Adaptive Learning Calibration
echo   5. Combined Optimal (All Strategies)
echo.
echo Each simulation takes ~2-3 minutes
echo Total estimated time: 10-15 minutes
echo.
echo Output files will be saved in the main project directory:
echo   - strategy1_results.csv to strategy5_results.csv
echo   - strategy1_summary.json to strategy5_summary.json
echo   - strategy_comparison_results.csv (final comparison)
echo   - strategy_comparison_summary.json (final summary)
echo.
echo ================================================================================
pause

python v2v_5_strategy_comparison.py

echo.
echo ================================================================================
echo Comparison complete! Check the generated CSV and JSON files for results.
echo ================================================================================
pause

