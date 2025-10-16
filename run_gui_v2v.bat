@echo off
echo Starting Enhanced V2V Simulation with GUI Control Panel...
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

echo All required files found. Starting enhanced V2V simulation with GUI control...
echo.
echo Features:
echo - Tkinter GUI Control Panel with zoom buttons
echo - Magenta vehicle (source) and Orange vehicle (destination)
echo - Green/Red highlighting based on V2V communication range
echo - Real-time status updates (distance, communication status)
echo - Pause/Resume and Single Step controls
echo - Automatic camera zoom to focus on V2V vehicles
echo.

REM Run the enhanced simulation
python focused_v2v_simulator.py

echo.
echo Enhanced V2V simulation completed. Check focused_v2v_results\ folder for outputs.
pause
