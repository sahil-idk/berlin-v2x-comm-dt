@echo off
echo Starting Sidelink V2V Simulation...
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
if not exist "sidelink_dataframe.parquet" (
    echo Error: sidelink_dataframe.parquet not found
    pause
    exit /b 1
)

if not exist "sumo-config\osm.sumocfg" (
    echo Error: sumo-config\osm.sumocfg not found
    pause
    exit /b 1
)

echo All required files found. Starting simulation...
echo.

REM Run the simulation
python simple_sidelink_simulation.py

echo.
echo Simulation completed. Check simulation_results\ folder for outputs.
pause
