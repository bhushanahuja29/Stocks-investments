@echo off
echo ======================================================================
echo Restarting Backend with New MongoDB Connection
echo ======================================================================
echo.

cd backend

echo Activating virtual environment...
call venv\Scripts\activate

echo.
echo Starting backend server...
echo Press Ctrl+C to stop
echo.

python main.py

pause
