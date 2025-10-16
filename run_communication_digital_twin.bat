@echo off
echo ======================================================================
echo V2V COMMUNICATION DIGITAL TWIN
echo ======================================================================
echo.
echo Features:
echo   - Inter-vehicular distance simulation (78%% baseline accuracy)
echo   - Path Loss Models: FSPL + 3GPP Urban Macro
echo   - SNR Calculation from simulated distances
echo   - Packet Reception Rate (PRR) estimation
echo   - Communication parameter accuracy validation
echo.
echo Output Files (saved to main project folder):
echo   - v2v_communication_analysis.csv (detailed per-waypoint analysis)
echo   - v2v_communication_summary.json (overall metrics)
echo.
echo ======================================================================
echo Starting simulation...
echo ======================================================================
echo.

python v2v_communication_digital_twin.py

echo.
echo ======================================================================
echo Simulation complete!
echo ======================================================================
pause

