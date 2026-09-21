"""
Fingerprint device bridge backends.

Priority:
  1. Hikvision FPModule_SDK.dll  (DS-K1F820-F)
  2. Neurotechnology Free Fingerprint Verification (Nffv)

Workers run in a child process so a native abort does not kill the HTTP bridge.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
LIB_DIR = DIR / "lib"
SDK_BIN = DIR / "sdk_free" / "FreeFingerprintVerification_3_1_SDK" / "Bin" / "Win64_x64"
TEMP_DIR = DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)

HIK_DLL = LIB_DIR / "FPModule_SDK.dll"
HIK_DLL_ALT = LIB_DIR / "hikvision" / "FPModule_SDK.dll"
HIK_WORKER = DIR / "_hik_worker.py"
NFFV_WORKER = DIR / "_nffv_worker.py"

NFFV_COMPANIONS = (
    "Neurotec.Biometrics.Nffv.xml",
    "NffvJavaNative.dll",
    "NffvServer.exe",
)


def _nffv_lib_dir() -> Path:
    """Use SDK Bin when present — lib/ copies often hit NffvInitialize IO/Operation errors."""
    if SDK_BIN.exists() and (SDK_BIN / "Nffv.dll").exists():
        return SDK_BIN
    return LIB_DIR


def _hik_dll_path() -> Path | None:
    if HIK_DLL.exists():
        return HIK_DLL
    if HIK_DLL_ALT.exists():
        return HIK_DLL_ALT
    return None


def _run_worker(
    worker: Path,
    *,
    action: str,
    timeout_sec: float,
    env_extra: dict[str, str],
) -> dict:
    if not worker.exists():
        return {"ok": False, "error": f"Missing worker script: {worker}", "code": 500}

    env = os.environ.copy()
    env.update(env_extra)
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        proc = subprocess.run(
            [sys.executable, str(worker)],
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
        return {"ok": False, "error": f"Failed to start worker: {exc}", "code": 500}

    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()

    if proc.returncode != 0:
        for line in reversed(stdout.splitlines()):
            line = line.strip()
            if line.startswith("{"):
                try:
                    payload = json.loads(line)
                    if isinstance(payload, dict):
                        return payload
                except json.JSONDecodeError:
                    break
        combined = f"{stdout}\n{stderr}".strip()
        if "avx2" in combined.lower() or proc.returncode == 7:
            return {
                "ok": False,
                "sdk": "Neurotechnology Free Fingerprint Verification (Nffv) 3.1",
                "error": (
                    "This PC/VM CPU does not support AVX2, which Nffv 3.1 requires. "
                    "Enable AVX2 in the VM settings, or run on a PC with AVX2."
                ),
                "code": 503,
                "detail": combined[:500],
            }
        return {
            "ok": False,
            "error": combined or f"Worker exited with code {proc.returncode}",
            "code": 500,
        }

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


def _run_hik(action: str, timeout_sec: float = 25.0) -> dict:
    dll = _hik_dll_path()
    if not dll:
        return {
            "ok": False,
            "backend": "hikvision",
            "error": (
                f"Missing {HIK_DLL}. Copy Hikvision Fingerprint Module SDK "
                "(FPModule_SDK.dll) into fingerprint_bridge/lib/."
            ),
            "code": 503,
        }
    return _run_worker(
        HIK_WORKER,
        action=action,
        timeout_sec=timeout_sec,
        env_extra={
            "HIK_LIB_DIR": str(dll.parent),
            "HIK_ACTION": action,
            "HIK_TIMEOUT": str(timeout_sec),
            "HIK_TEMP": str(TEMP_DIR),
        },
    )


def _run_nffv(action: str, timeout_sec: float = 25.0) -> dict:
    lib_dir = _nffv_lib_dir()
    dll = lib_dir / "Nffv.dll"
    if not dll.exists():
        return {
            "ok": False,
            "backend": "nffv",
            "error": (
                f"Missing {dll}. Copy FreeFingerprintVerification "
                "Bin\\Win64_x64 into fingerprint_bridge\\lib\\"
            ),
            "code": 503,
        }
    result = _run_worker(
        NFFV_WORKER,
        action=action,
        timeout_sec=timeout_sec,
        env_extra={
            "NFFV_LIB_DIR": str(lib_dir),
            "NFFV_ACTION": action,
            "NFFV_TIMEOUT": str(timeout_sec),
            "NFFV_TEMP": str(TEMP_DIR),
        },
    )
    result.setdefault("backend", "nffv")
    return result


def _active_backend() -> str:
    """Default to Hikvision — this project targets DS-K1F820-F."""
    forced = (os.environ.get("FP_BACKEND") or "").strip().lower()
    if forced in ("nffv", "neurotec", "free"):
        return "nffv"
    if forced in ("hikvision", "hik", "ds-k1f820-f"):
        return "hikvision"
    # Prefer Hikvision whenever the DLL exists; otherwise still default to
    # hikvision so capture never falls through to Nffv's "use Futronic" error.
    return "hikvision"


def _usb_hint() -> str:
    return (
        "Also check Device Manager: the DS-K1F820-F must not show "
        "'Unknown USB Device (Device Descriptor Request Failed)'. "
        "Try another USB port/cable (direct PC port, not a hub)."
    )


def sdk_status() -> dict:
    backend = _active_backend()
    if backend == "hikvision":
        result = _run_hik("status", timeout_sec=10)
        result.setdefault("sdk", "Hikvision FPModule SDK (DS-K1F820-F)")
        result.setdefault("dll", str(_hik_dll_path()) if _hik_dll_path() else str(HIK_DLL))
        if not result.get("ok"):
            err = str(result.get("error") or "")
            if "Missing" in err and _usb_hint() not in err:
                result["error"] = err.rstrip(".") + ". " + _usb_hint()
            result.setdefault(
                "note",
                "Nffv cannot drive DS-K1F820-F. Use Hikvision FPModule_SDK.dll "
                "(set FP_BACKEND=nffv only for Futronic/SecuGen/etc.).",
            )
        return result

    result = _run_nffv("status", timeout_sec=10)
    result.setdefault("sdk", "Neurotechnology Free Fingerprint Verification (Nffv) 3.1")
    result.setdefault("dll", str(_nffv_lib_dir() / "Nffv.dll"))
    result.setdefault(
        "note",
        "FP_BACKEND=nffv is active. For DS-K1F820-F use Hikvision FPModule instead.",
    )
    return result


def capture_fingerprint(timeout_sec: float = 25.0) -> dict:
    backend = _active_backend()
    if backend == "nffv":
        return _run_nffv("capture", timeout_sec=timeout_sec)
    # Hikvision only — do not fall back to Nffv (that yields a misleading error).
    return _run_hik("capture", timeout_sec=timeout_sec)


def hamming_hex(a: str, b: str) -> int:
    a = (a or "").strip().lower()
    b = (b or "").strip().lower()
    if not a or not b or len(a) != len(b):
        return 999
    try:
        return bin(int(a, 16) ^ int(b, 16)).count("1")
    except ValueError:
        return 999
