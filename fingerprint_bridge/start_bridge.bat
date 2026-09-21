@echo off
cd /d "%~dp0"
setlocal EnableExtensions

echo ============================================================
echo  Fingerprint Bridge launcher (Hikvision DS-K1F820-F)
echo ============================================================
echo.

REM Prefer 32-bit Python — FPModule_SDK.dll is usually x86
set "PYEXE="
where py >nul 2>&1
if not errorlevel 1 (
  py -3.11-32 -c "import sys" >nul 2>&1
  if not errorlevel 1 set "PYEXE=py -3.11-32"
  if not defined PYEXE (
    py -3-32 -c "import sys" >nul 2>&1
    if not errorlevel 1 set "PYEXE=py -3-32"
  )
)
if not defined PYEXE set "PYEXE=python"

echo Using: %PYEXE%
%PYEXE% -c "import struct; print(' Python bits:', struct.calcsize('P')*8)"

if not exist "lib\FPModule_SDK.dll" (
  echo.
  echo [BLOCKED] Missing lib\FPModule_SDK.dll
  echo.
  echo This bridge cannot talk to DS-K1F820-F without Hikvision's SDK DLL.
  echo Nffv / Futronic / SecuGen SDKs will NOT work for this device.
  echo.
  echo How to get it:
  echo   1. Ask your Hikvision distributor for "Fingerprint Module SDK"
  echo      ^(FPModule_SDK.dll, often 32-bit^).
  echo   2. Or install iVMS-4200 / the enrollment tools that shipped with
  echo      the recorder, then search your PC for FPModule_SDK.dll and
  echo      copy it into fingerprint_bridge\lib\
  echo   3. Also fix USB: Device Manager must NOT show
  echo      "Unknown USB Device (Device Descriptor Request Failed)".
  echo.
  echo After copying the DLL, run this bat again.
  echo.
  pause
  exit /b 1
)

%PYEXE% -c "import PIL" 2>nul
if errorlevel 1 (
  echo Installing Pillow...
  %PYEXE% -m pip install -r requirements.txt
)

echo.
echo Starting bridge on http://127.0.0.1:8765 ...
echo.
%PYEXE% app.py
pause
