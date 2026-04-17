@echo off
echo ========================================
echo Fixing Dependencies and System Issues
echo ========================================
echo.

echo [1/3] Uninstalling scikit-learn 1.8.0...
call venv\Scripts\activate
pip uninstall -y scikit-learn
echo.

echo [2/3] Installing scikit-learn 1.6.1 (matching trained models)...
pip install scikit-learn==1.6.1
echo.

echo [3/3] Verifying installation...
python -c "import sklearn; print(f'scikit-learn version: {sklearn.__version__}')"
echo.

echo ========================================
echo Fix complete!
echo ========================================
echo.
echo To avoid WinError 1450 (file handle exhaustion):
echo 1. Close unnecessary programs
echo 2. Restart your terminal
echo 3. Run: uvicorn app.main:app --reload --port 8000
echo.
pause
