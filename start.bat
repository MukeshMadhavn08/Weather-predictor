@echo off
echo Starting IoT Weather App...

echo [1/2] Starting FastAPI Backend on port 8000...
start "Backend" cmd /k "cd /d D:\project\backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 3 /nobreak >nul

echo [2/2] Starting Next.js Frontend on port 3000...
start "Frontend" cmd /k "cd /d D:\project\frontend && npm run dev"

echo.
echo Both servers are starting. Open your browser at:
echo   http://localhost:3000
echo.
pause
