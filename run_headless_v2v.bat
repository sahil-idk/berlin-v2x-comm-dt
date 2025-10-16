@echo off
REM Headless V2V Distance Validation Batch Script
REM This script runs the headless V2V simulation for distance validation

echo Starting Headless V2V Distance Validation...

REM Create headless configuration
echo Creating headless configuration...
python create_headless_config.py
if %errorlevel% neq 0 (
    echo Failed to create headless configuration
    pause
    exit /b 1
)

REM Run distance validation
echo Running distance validation...
python headless_v2v_distance_validation.py
if %errorlevel% neq 0 (
    echo Distance validation failed
    pause
    exit /b 1
)

echo Distance validation completed successfully!
pause
