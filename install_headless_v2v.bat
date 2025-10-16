@echo Installing Headless V2V Validation Suite...

REM Install any required Python packages
python -m pip install pandas numpy traci

REM Create headless configuration
echo Creating headless configuration...
python create_headless_config.py

REM Run a test validation
echo Running test validation...
python headless_v2v_distance_validation.py

echo Installation and test completed!
echo Check the generated reports for results.
pause
