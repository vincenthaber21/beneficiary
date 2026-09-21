@echo off
cd /d "%~dp0"
echo Checking fingerprint bridge readiness...
echo.

if exist "lib\FPModule_SDK.dll" (
  echo [OK] lib\FPModule_SDK.dll found
) else (
  echo [MISSING] lib\FPModule_SDK.dll
  echo   Get Hikvision Fingerprint Module SDK from your distributor / iVMS package
  echo   and copy FPModule_SDK.dll into this lib\ folder.
  echo.
)

python -c "import struct; print('[INFO] Python is', struct.calcsize('P')*8, 'bit')"
python -c "import fp_device as fp, json; s=fp.sdk_status(); print('[STATUS]', 'OK' if s.get('ok') else 'NOT READY'); print(s.get('error') or s.get('sdk'));"

echo.
echo If Device Manager shows Unknown USB Device, unplug the DS-K1F820-F,
echo use a different USB cable/port (direct to PC), then replug.
echo.
pause
