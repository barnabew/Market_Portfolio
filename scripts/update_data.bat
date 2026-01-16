@echo off
cd /d "D:\market"
echo.
echo ----------------------------------------
echo Updating market data...
echo ----------------------------------------
echo.

REM Run recup_data.py
python recup_data.py

echo.
echo ----------------------------------------
echo Managing user portfolio
echo ----------------------------------------
echo.

REM Run wallet.py
python wallet.py

echo.
echo ----------------------------------------
echo Process completed. Press any key to close.
echo ----------------------------------------
pause > nul