@echo off
echo ========================================
echo Embedded Closer V2V Visualization
echo ========================================
echo.
echo This will:
echo 1. Convert CSV to embedded HTML (if needed)
echo 2. Open the embedded visualization in your browser
echo.
echo The embedded version has all data included in the HTML file,
echo so it works without needing the CSV file.
echo.
pause

echo.
echo Step 1: Converting CSV to embedded HTML...
python convert_csv_to_embedded_html.py

if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to convert CSV to embedded HTML
    pause
    exit /b 1
)

echo.
echo Step 2: Opening embedded visualization...
python open_embedded_closer_visualization.py

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Files created:
echo - closer_v2v_visualization_embedded.html (standalone visualization)
echo.
echo The embedded visualization should now be open in your browser.
echo This version has all data embedded and works without CSV dependencies.
echo.
pause
