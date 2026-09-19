"""
Neurotechnology Free Fingerprint Verification SDK (Nffv) wrapper.

Loads Nffv.dll in a child process so an AVX2/CPU abort does not kill the bridge.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
LIB_DIR = DIR / "lib"
NFFV_DLL = LIB_DIR / "Nffv.dll"
TEMP_DIR = DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)
WORKER = DIR / "_nffv_worker.py"


def _run_worker(action: str, timeout_sec: float = 30.0) -> dict:
    if not NFFV_DLL.exists():
        return {
            "ok": False,
            "error": (
                f"Missing {NFFV_DLL}. Copy FreeFingerprintVerification "
                "Bin\\Win64_x64 into fingerprint_bridge\\lib\\"
            ),
            "code": 503,
        }
    if not WORKER.exists():
        return {"ok": False, "error": f"Missing worker script: {WORKER}", "code": 500}

    env = os.environ.copy()
    env["NFFV_LIB_DIR"] = str(LIB_DIR)
    env["NFFV_ACTION"] = action
    env["NFFV_TIMEOUT"] = str(timeout_sec)
    env["NFFV_TEMP"] = str(TEMP_DIR)
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        proc = subprocess.run(
            [sys.executable, str(WORKER)],
            capture_output=True,
            text=True,
            timeout=max(35.0, timeout_sec + 15.0),
            env=env,
            cwd=str(DIR),
        )
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "error": "Fingerprint scanner timed out waiting for a finger.",
            "code": 408,
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"Failed to start Nffv worker: {exc}", "code": 500}

    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()

    if proc.returncode != 0:
        combined = f"{stdout}\n{stderr}".strip()
        if "avx2" in combined.lower() or proc.returncode == 7:
            return {
                "ok": False,
                "sdk": "Neurotechnology Free Fingerprint Verification (Nffv) 3.1",
                "error": (
                    "This PC/VM CPU does not support AVX2, which Nffv 3.1 requires. "
                    "Enable AVX2 in the VM settings, or run on a PC with AVX2 "
                    "(most Intel Core i3/i5/i7 and AMD Ryzen from ~2013+)."
                ),
                "code": 503,
                "detail": combined[:500],
            }
        return {
            "ok": False,
            "error": combined or f"Nffv worker exited with code {proc.returncode}",
            "code": 500,
        }

    # Worker prints one JSON object on the last non-empty line
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return {
        "ok": False,
        "error": f"Unexpected worker output: {stdout[:400] or stderr[:400]}",
        "code": 500,
    }


def sdk_status() -> dict:
    result = _run_worker("status", timeout_sec=10)
    result.setdefault("sdk", "Neurotechnology Free Fingerprint Verification (Nffv) 3.1")
    result.setdefault("dll", str(NFFV_DLL))
    result.setdefault(
        "note",
        "Hikvision DS-K1F820-F is not in Nffv's scanner list. "
        "Supported brands are under lib/FScanners/ (Futronic, SecuGen, "
        "DigitalPersona/Upek, ZKTeco, Suprema, Nitgen, …).",
    )
    return result


def capture_fingerprint(timeout_sec: float = 25.0) -> dict:
    return _run_worker("capture", timeout_sec=timeout_sec)


def hamming_hex(a: str, b: str) -> int:
    a = (a or "").strip().lower()
    b = (b or "").strip().lower()
    if not a or not b or len(a) != len(b):
        return 999
    try:
        return bin(int(a, 16) ^ int(b, 16)).count("1")
    except ValueError:
        return 999
