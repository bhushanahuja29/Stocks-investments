@echo off
echo Restarting Backend Server...
echo.

REM Kill processes on port 8000
echo Stopping backend on port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do taskkill /F /PID %%a 2>nul

timeout /t 2 /nobreak >nul

REM Start backend
echo Starting backend...
cd backend
call ..\venv\Scripts\activate.bat
start "Backend Server" cmd /k "uvicorn main:app --reload --host 0.0.0.0 --port 8000"

echo.
echo Backend restarted!
echo Check the "Backend Server" window for logs.
pause
