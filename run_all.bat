@echo off
echo Starting NVIDIA Bio-Powered MedQuery System...

:: Start the FastAPI mock server in a new window
start "MedQuery Mock Server" cmd /k "cd /d %~dp0 && .\.venv\Scripts\activate && uvicorn app.server.main:app --reload --port 8000"

:: Wait 8 seconds for server to start
echo.
echo Waiting 8 seconds for mock server to start...
timeout /t 8 >nul

:: Open browser to Swagger UI (optional but helpful)
start http://127.0.0.1:8000/docs

:: Run the main MedQuery script
echo.
echo Starting MedQuery Intelligence Engine...
.\.venv\Scripts\python.exe -m scripts.run_medquery

:: Keep window open after finish
pause