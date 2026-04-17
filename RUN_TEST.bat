@echo off
echo ========================================
echo FACT-CHECK SYSTEM TEST
echo ========================================
echo.

echo Checking if backend is running...
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Backend is not running!
    echo.
    echo Please start the backend first:
    echo   1. Open a new terminal
    echo   2. cd backend
    echo   3. venv\Scripts\activate
    echo   4. uvicorn app.main:app --port 8000
    echo.
    echo Then run this test again.
    pause
    exit /b 1
)

echo Backend is running!
echo.
echo Running tests...
echo.

python test_claim_simple.py

echo.
pause
