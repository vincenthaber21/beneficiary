# Fingerprint Feature — New PC Setup Guide

This project uses a **Hikvision DS-K1F820-F** fingerprint recorder. Django talks to a small local bridge on **http://127.0.0.1:8765**. When you run:

```bat
python manage.py runserver
```

you should see:

```text
Fingerprint bridge already running on http://127.0.0.1:8765
```

or:

```text
Fingerprint bridge started (pid …) via py -3.11-32 on http://127.0.0.1:8765
```

That means the fingerprint service is ready. You do **not** need a second terminal for normal use.

---

## What to download / install on a new PC

| # | Software | Why | Download / notes |
|---|----------|-----|------------------|
| 1 | **Python 3.11+ (64-bit)** | Runs Django (`manage.py runserver`) | [python.org](https://www.python.org/downloads/) — check **“Add python.exe to PATH”** |
| 2 | **Python 3.11 32-bit** | Required for Hikvision `FPModule_SDK.dll` (usually 32-bit) | Same site → Windows installer → **Windows installer (32-bit)** |
| 3 | **Git** (optional) | Copy the project from another PC / repo | [git-scm.com](https://git-scm.com/) |
| 4 | **Hikvision Fingerprint Module SDK** | Provides `FPModule_SDK.dll` | From your Hikvision distributor, or from **iVMS-4200** / enrollment tools that shipped with the device |
| 5 | **USB cable + DS-K1F820-F** | Physical scanner | Plug into a **direct motherboard USB port** (avoid hubs) |
| 6 | **Visual C++ Redistributable** (if DLL fails to load) | Runtime for SDK / Nffv DLLs | [Microsoft VC++ x86](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist) — install **x86** (32-bit) |

> **Important:** You need **both** 64-bit Python (for Django) and **32-bit Python 3.11** (for the fingerprint bridge). The launcher looks for `py -3.11-32`.

---

## One-time project setup (copy checklist)

### 1. Copy the project folder

Copy the whole `beneficiary` folder to the new PC (or clone the repo). Keep this folder intact:

```text
beneficiary/
  manage.py
  requirements.txt
  fingerprint_bridge/
    app.py
    start_bridge.bat
    check_setup.bat
    lib/
      FPModule_SDK.dll     ← must exist
      …other SDK files…
```

### 2. Put the Hikvision DLL in place

If `fingerprint_bridge\lib\FPModule_SDK.dll` is missing:

1. Get **Fingerprint Module SDK** from Hikvision / your distributor, **or**
2. Install iVMS-4200 / the enrollment tools that came with the recorder, then search the PC for `FPModule_SDK.dll`.
3. Copy it to:

```text
fingerprint_bridge\lib\FPModule_SDK.dll
```

Without this file, the DS-K1F820-F **will not work**. Neurotechnology Nffv / Futronic / SecuGen SDKs cannot drive this Hikvision device.

### 3. Install Python packages

Open **Command Prompt** or **PowerShell** in the project folder:

```bat
cd C:\Users\YOUR_NAME\Desktop\sonney_system\beneficiary

REM Django (use your normal / 64-bit Python)
python -m pip install -r requirements.txt

REM Bridge deps on 32-bit Python
py -3.11-32 -m pip install -r fingerprint_bridge\requirements.txt
```

Confirm 32-bit Python is really 32-bit:

```bat
py -3.11-32 -c "import struct; print(struct.calcsize('P')*8)"
```

Must print `32`.

### 4. Database (first time only)

```bat
python manage.py migrate
python manage.py createsuperuser
```

(Skip `createsuperuser` if you already copied `db.sqlite3` with users.)

### 5. Plug in the scanner and fix USB if needed

1. Connect the **DS-K1F820-F** with a good USB cable.
2. Open **Device Manager**.
3. The device must **not** show:

   `Unknown USB Device (Device Descriptor Request Failed)` (Code 43)

If it does: try another cable/port, use a rear motherboard port (not a hub), unplug/replug, reboot.

### 6. Quick readiness check (optional)

```bat
cd fingerprint_bridge
check_setup.bat
```

Or open in a browser after the bridge is up:

```text
http://127.0.0.1:8765/status
```

You want a response with `"ok": true` (or similar success).

---

## Everyday use (after setup)

### Start the system

From the project folder:

```bat
python manage.py runserver
```

Django auto-starts the fingerprint bridge on port **8765**.  
Open the site (usually **http://127.0.0.1:8000/**).

### Where to use fingerprints in the app

| Page | Action |
|------|--------|
| **Citizens → Add / Edit** | **Scan Finger** to enroll |
| **Beneficiaries → Add / Edit** | **Scan Finger** to enroll |
| **ID / Fingerprint Tap** (checker) | **Scan Fingerprint** to look up / verify |

### Manual bridge start (only if auto-start fails)

```bat
cd fingerprint_bridge
start_bridge.bat
```

Or:

```bat
cd fingerprint_bridge
py -3.11-32 app.py
```

Then start Django in another window: `python manage.py runserver`.

---

## Environment options (advanced)

| Variable | Meaning |
|----------|---------|
| `FINGERPRINT_BRIDGE_AUTOSTART=0` | Do not auto-start bridge with `runserver` |
| `FINGERPRINT_BRIDGE_PYTHON=...` | Force which Python runs the bridge (must be 32-bit for Hikvision) |
| `FP_BACKEND=hikvision` | Force Hikvision backend |
| `FP_BACKEND=nffv` | Force Nffv (other scanner brands only) |

Example (PowerShell):

```powershell
$env:FINGERPRINT_BRIDGE_AUTOSTART="0"
python manage.py runserver
```

---

## Troubleshooting

| Problem | What to do |
|---------|------------|
| Message: *Could not start fingerprint bridge… no 32-bit Python* | Install **Python 3.11 32-bit**; verify with `py -3.11-32 -c "import struct; print(struct.calcsize('P')*8)"` → `32` |
| *Missing lib\FPModule_SDK.dll* | Copy Hikvision DLL into `fingerprint_bridge\lib\` |
| Browser: *Fingerprint bridge offline* | Bridge not on 8765 — run `start_bridge.bat` or restart `runserver` |
| Status not OK / device won’t open | Fix USB in Device Manager; try another port/cable; reboot |
| Wrong Python for bridge | Set `FINGERPRINT_BRIDGE_PYTHON` to your 32-bit `python.exe` path |
| Port already in use | Message *already running* is **OK** — leave it; or close the old `python`/`app.py` process and restart |

---

## Minimal “new PC” packing list

Copy / install these and you are done:

1. Entire `beneficiary` project folder (including `fingerprint_bridge\lib\FPModule_SDK.dll`)
2. Python **64-bit** + Python **3.11 32-bit**
3. `pip install -r requirements.txt` and `py -3.11-32 -m pip install -r fingerprint_bridge\requirements.txt`
4. Hikvision **DS-K1F820-F** + USB cable
5. Run: `python manage.py runserver`

More technical detail: see `fingerprint_bridge/README.md`.
