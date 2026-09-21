# Fingerprint bridge — Hikvision DS-K1F820-F + optional Nffv

## Your device: Hikvision DS-K1F820-F

Neurotechnology **Nffv cannot drive** the DS-K1F820-F. This bridge uses Hikvision’s
`FPModule_SDK.dll` when present.

### 1. Get the SDK DLL

Obtain **Fingerprint Module SDK** from Hikvision / your distributor (or extract
`FPModule_SDK.dll` from the enrollment tools that ship with the device / iVMS-4200).

Copy it here:

```
fingerprint_bridge/lib/FPModule_SDK.dll
```

### 2. Python architecture must match the DLL

Many Hikvision builds of `FPModule_SDK.dll` are **32-bit**. This PC now has
32-bit Python 3.11. Prefer:

```bat
py -3.11-32 -m pip install -r requirements.txt
py -3.11-32 app.py
```

Or just run `start_bridge.bat` (it picks 32-bit Python automatically).

Do **not** use `py -3-32` — that alias is not registered; use `py -3.11-32`.

Check bits:

```bat
py -3.11-32 -c "import struct; print(struct.calcsize('P')*8)"
```

Should print `32`.

### 3. USB must enumerate cleanly

In Device Manager the recorder must **not** show:

`Unknown USB Device (Device Descriptor Request Failed)` (Code 43)

If it does: try another USB port/cable, a direct motherboard port (not a hub),
unplug/replug, then reboot. Without a healthy USB device the SDK cannot open it.

### 4. Start the bridge

```bat
cd fingerprint_bridge
pip install -r requirements.txt
python app.py
```

Or `start_bridge.bat`.

Check: http://127.0.0.1:8765/status

## Optional: Nffv (other scanner brands)

Nffv supports Futronic, SecuGen, DigitalPersona/Upek, ZKTeco, Suprema, Nitgen, …

SDK files live under `lib/` (or `sdk_free/.../Bin/Win64_x64`). Required companions
next to `Nffv.dll`:

- `Neurotec.Biometrics.Nffv.xml`
- `NffvJavaNative.dll`
- `NffvServer.exe`
- `FScanners\`

Force a backend:

```bat
set FP_BACKEND=hikvision
set FP_BACKEND=nffv
```

## API

| Method | URL | Purpose |
|--------|-----|---------|
| GET | `/status` | SDK + scanners |
| GET | `/capture` | Capture finger → hash + PNG |
| POST | `/match` | Live scan vs sample hashes |

## Use in the app

1. Keep this bridge running  
2. Keep Django running (`python manage.py runserver`)  
3. Citizens → Add → Scan Finger  
4. ID / Fingerprint Tap → Scan Fingerprint  
