@echo off
echo Starting Focused V2V Simulation (2 vehicles with highlighting)...
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

echo All required files found. Starting focused V2V simulation...
echo This will simulate only 2 vehicles with V2V communication highlighting.
echo.

REM Run the focused simulation
python focused_v2v_simulator.py

echo.
echo Focused V2V simulation completed. Check focused_v2v_results\ folder for outputs.
pause
