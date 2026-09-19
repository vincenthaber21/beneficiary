@echo off
cd /d "%~dp0"
echo Starting Free Fingerprint Verification (Nffv) bridge...
echo.
if not exist "lib\Nffv.dll" (
  echo ERROR: lib\Nffv.dll not found.
  echo Extract FreeFingerprintVerification_3_1_SDK Bin\Win64_x64 into lib\
  echo.
  pause
  exit /b 1
)
python -c "import PIL" 2>nul
if errorlevel 1 (
  echo Installing Pillow...
  pip install -r requirements.txt
)
python app.py
pause
