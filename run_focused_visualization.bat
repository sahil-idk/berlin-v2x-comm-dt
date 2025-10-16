@echo off
echo ========================================
echo Focused V2V Visualization Setup
echo ========================================
echo.
echo This will:
echo 1. Extract Vehicle 2-4 interaction dataset
echo 2. Create focused HTML visualization
echo 3. Open the visualization in your browser
echo.
pause

echo.
echo Step 1: Extracting Vehicle 2-4 dataset...
python extract_vehicle_2_4_dataset.py

if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to extract dataset
    pause
    exit /b 1
)

echo.
echo Step 2: Opening focused visualization...
echo Opening focused_v2v_visualization.html in your default browser...

start focused_v2v_visualization.html

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Files created:
echo - vehicle_2_4_focused.csv (focused dataset)
echo - vehicle_2_4_metadata.json (dataset metadata)
echo - focused_v2v_visualization.html (visualization)
echo.
echo The visualization should now be open in your browser.
echo You can interact with the map to see Vehicle 2-4 V2V communication.
echo.
pause
