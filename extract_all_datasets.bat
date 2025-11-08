@echo off
echo ============================================================
echo V2V Digital Twin - Extract All Dataset Sizes
echo ============================================================
echo.

echo [1/3] Extracting 200-point dataset...
python extract_vehicle_2_4_dataset.py --preset 200
echo.

echo [2/3] Extracting 500-point dataset...
python extract_vehicle_2_4_dataset.py --preset 500
echo.

echo [3/3] Extracting 1000-point dataset...
python extract_vehicle_2_4_dataset.py --preset 1000
echo.

echo ============================================================
echo All datasets extracted successfully!
echo ============================================================
echo.
echo Files created:
echo   - vehicle_2_4_200.csv
echo   - vehicle_2_4_500.csv
echo   - vehicle_2_4_1000.csv
echo.
echo Next step: Run python v2v_communication_digital_twin.py
echo.
pause

