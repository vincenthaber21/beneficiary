# Free Fingerprint Verification SDK (Nffv) — setup

This bridge uses the SDK from:

`FreeFingerprintVerification_3_1_SDK_2026-03-30.zip`

(Neurotechnology Free Fingerprint Verification 3.1)

## Already done in this project

SDK binaries were copied to:

```
fingerprint_bridge/lib/Nffv.dll
fingerprint_bridge/lib/FScanners/...
```

## Start the bridge

```bat
cd d:\beneficiary-checker\fingerprint_bridge
pip install -r requirements.txt
python app.py
```

Or run `start_bridge.bat`.

Check: http://127.0.0.1:8765/status

## Use in the app

1. Keep the bridge running
2. Keep Django running (`python manage.py runserver`)
3. Open http://127.0.0.1:8000/citizens/add/
4. Choose a finger → **Scan Finger** → place finger on scanner → **Save**

On **ID / Fingerprint Tap**, use **Scan with fingerprint scanner**.

## Important: CPU requirement (AVX2)

Nffv 3.1 requires a CPU with **AVX2**. If `/status` says AVX2 is missing:

- On a **VM**: enable AVX2 / nested virtualization CPU features, or
- Run on a physical PC with AVX2 (most Intel Core / AMD Ryzen from ~2013+)

## Important: scanner compatibility

Nffv supports modules under `lib/FScanners/` such as:

- Futronic, SecuGen, DigitalPersona/Upek, ZKTeco, Suprema, Nitgen, Lumidigm, …

**Hikvision DS-K1F820-F is not in this SDK’s scanner list.**  
If `/status` shows `"NoScanner"` or an empty scanner list when only the Hikvision device is plugged in, the Free Fingerprint Verification SDK cannot drive that recorder. You would need a scanner brand listed above, or Hikvision’s own `FPModule_SDK.dll`.

## Optional: limit scanner modules

```bat
set NFFV_SCANNERS=Futronic;SecuGen
python app.py
```

## API

| Method | URL | Purpose |
|--------|-----|---------|
| GET | `/status` | SDK + available scanners |
| GET | `/capture` | Enroll one finger, return hash + PNG |
| POST | `/match` | Live scan vs sample hashes |
