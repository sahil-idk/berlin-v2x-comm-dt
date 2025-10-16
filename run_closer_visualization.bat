@echo off
echo ========================================
echo Closer V2V Visualization Setup
echo ========================================
echo.
echo This will:
echo 1. Extract Vehicle 2-4 closer points dataset
echo 2. Create closer HTML visualization
echo 3. Open the visualization in your browser
echo.
pause

echo.
echo Step 1: Extracting closer Vehicle 2-4 dataset...
python extract_closer_vehicle_2_4_dataset.py

if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to extract closer dataset
    pause
    exit /b 1
)

echo.
echo Step 2: Opening closer visualization...
echo Opening closer_v2v_visualization.html in your default browser...

start closer_v2v_visualization.html

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Files created:
echo - vehicle_2_4_closer_points.csv (closer dataset)
echo - vehicle_2_4_closer_metadata.json (dataset metadata)
echo - closer_v2v_visualization.html (closer visualization)
echo.
echo The closer visualization should now be open in your browser.
echo This shows Vehicle 2-4 interactions with much closer GPS points
echo for better visibility of V2V communication.
echo.
pause
