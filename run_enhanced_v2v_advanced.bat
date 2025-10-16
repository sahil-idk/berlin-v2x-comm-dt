@echo off
echo Starting Enhanced V2V Simulation with Advanced Features...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if SUMO is available
sumo --version >nul 2>&1
if errorlevel 1 (
    echo Error: SUMO is not installed or not in PATH
    echo Please install SUMO and add it to your PATH
    pause
    exit /b 1
)

REM Check if required files exist
if not exist "sidelink_parsed.csv" (
    echo Error: sidelink_parsed.csv not found
    pause
    exit /b 1
)

if not exist "sumo-config\osm.sumocfg" (
    echo Error: sumo-config\osm.sumocfg not found
    pause
    exit /b 1
)

echo All required files found. Starting enhanced V2V simulation...
echo.
echo NEW FEATURES:
echo - Dynamic camera following and rotation around V2V vehicles
echo - Enhanced V2V link simulation with quality assessment
echo - Scrollable GUI panel showing real-time CSV row data
echo - Integration with ~50 rows from sidelink_parsed.csv
echo - Advanced vehicle highlighting and communication visualization
echo - Real-time distance, communication status, and V2V link monitoring
echo.

REM Run the enhanced simulation
python focused_v2v_simulator.py

echo.
echo Enhanced V2V simulation completed. Check focused_v2v_results\ folder for outputs.
pause
