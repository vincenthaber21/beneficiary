"""Child process that loads Nffv.dll and performs status/capture."""

from __future__ import annotations

import base64
import io
import json
import os
import sys
from ctypes import (
    POINTER,
    byref,
    c_char_p,
    c_float,
    c_int,
    c_ubyte,
    c_uint,
    c_void_p,
    create_string_buffer,
)
import ctypes
from pathlib import Path

NFES_TEMPLATE_CREATED = 1
NFES_NO_SCANNER = 2
NFES_SCANNER_TIMEOUT = 3
NFES_QUALITY_CHECK_FAILED = 100

STATUS_LABELS = {
    0: "None",
    1: "TemplateCreated",
    2: "NoScanner",
    3: "ScannerTimeout",
    4: "UserCanceled",
    100: "QualityCheckFailed",
}


def _emit(payload: dict):
    print(json.dumps(payload), flush=True)


def main():
    lib_dir = Path(os.environ.get("NFFV_LIB_DIR", ""))
    action = os.environ.get("NFFV_ACTION", "status")
    timeout_sec = float(os.environ.get("NFFV_TIMEOUT", "25"))
    temp_dir = Path(os.environ.get("NFFV_TEMP", "."))
    temp_dir.mkdir(parents=True, exist_ok=True)

    dll_path = lib_dir / "Nffv.dll"
    if not dll_path.exists():
        _emit({"ok": False, "error": f"Missing {dll_path}", "code": 503})
        return 1

    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(str(lib_dir))
        fscan = lib_dir / "FScanners"
        if fscan.exists():
            os.add_dll_directory(str(fscan))
            for sub in fscan.iterdir():
                if sub.is_dir():
                    os.add_dll_directory(str(sub))
    os.environ["PATH"] = str(lib_dir) + os.pathsep + os.environ.get("PATH", "")

    try:
        lib = ctypes.WinDLL(str(dll_path))
    except OSError as exc:
        _emit({"ok": False, "error": f"Failed to load Nffv.dll: {exc}", "code": 503})
        return 1

    lib.NffvGetAvailableScannerModulesA.argtypes = [POINTER(c_char_p)]
    lib.NffvGetAvailableScannerModulesA.restype = c_int
    lib.NffvInitializeA.argtypes = [c_char_p, c_char_p, c_char_p]
    lib.NffvInitializeA.restype = c_int
    lib.NffvUninitialize.argtypes = []
    lib.NffvUninitialize.restype = None
    lib.NffvEnroll.argtypes = [c_uint, POINTER(c_int), POINTER(c_void_p)]
    lib.NffvEnroll.restype = c_int
    lib.NffvClearUsers.argtypes = []
    lib.NffvClearUsers.restype = c_int
    lib.NffvUserGetId.argtypes = [c_void_p, POINTER(c_int)]
    lib.NffvUserGetId.restype = c_int
    lib.NffvUserGetImage.argtypes = [
        c_void_p,
        POINTER(c_uint),
        POINTER(c_uint),
        POINTER(c_float),
        POINTER(c_float),
        POINTER(ctypes.c_size_t),
        c_void_p,
    ]
    lib.NffvUserGetImage.restype = c_int
    lib.NffvFreeMemory.argtypes = [c_void_p]
    lib.NffvFreeMemory.restype = None
    lib.NffvGetErrorMessageA.argtypes = [c_int, c_char_p]
    lib.NffvGetErrorMessageA.restype = c_int
    lib.NffvSetQualityThreshold.argtypes = [c_ubyte]
    lib.NffvSetQualityThreshold.restype = c_int

    def err_msg(code: int) -> str:
        buf = create_string_buffer(1024)
        n = lib.NffvGetErrorMessageA(code, buf)
        if n > 0 and buf.value:
            return buf.value.decode("ascii", errors="ignore")
        return f"NResult={code}"

    def available_modules() -> list[str]:
        ptr = c_char_p()
        result = lib.NffvGetAvailableScannerModulesA(byref(ptr))
        if result != 0:
            return []
        try:
            raw = ptr.value.decode("ascii", errors="ignore") if ptr.value else ""
        finally:
            if ptr:
                lib.NffvFreeMemory(ptr)
        return [m for m in raw.split(";") if m.strip()] if raw else []

    modules = available_modules()
    module_str = os.environ.get("NFFV_SCANNERS", "").strip() or ";".join(modules)
    db_path = temp_dir / "nffv_bridge.dat"
    init = lib.NffvInitializeA(
        str(db_path).encode("ascii", errors="ignore"),
        b"",
        module_str.encode("ascii", errors="ignore"),
    )
    if init != 0:
        _emit(
            {
                "ok": False,
                "error": f"NffvInitialize failed: {err_msg(init)}",
                "code": 500,
                "available_scanners": modules,
            }
        )
        return 1

    try:
        lib.NffvSetQualityThreshold(c_ubyte(40))
    except Exception:
        pass

    if action == "status":
        _emit(
            {
                "ok": True,
                "initialized": True,
                "available_scanners": modules,
                "active_scanners": module_str.split(";") if module_str else [],
                "error": None,
            }
        )
        lib.NffvUninitialize()
        return 0

    from PIL import Image

    status = c_int(0)
    h_user = c_void_p()
    timeout_ms = max(1000, int(timeout_sec * 1000))
    result = lib.NffvEnroll(c_uint(timeout_ms), byref(status), byref(h_user))
    if result != 0:
        _emit({"ok": False, "error": f"NffvEnroll failed: {err_msg(result)}", "code": 500})
        lib.NffvUninitialize()
        return 1

    st = int(status.value)
    if st != NFES_TEMPLATE_CREATED or not h_user:
        label = STATUS_LABELS.get(st, str(st))
        hints = {
            NFES_NO_SCANNER: (
                "No compatible scanner detected. "
                "Nffv does not support Hikvision DS-K1F820-F. "
                "Use Futronic, SecuGen, DigitalPersona, ZKTeco, Suprema, Nitgen, etc."
            ),
            NFES_SCANNER_TIMEOUT: "No finger detected in time. Place finger on the scanner and retry.",
            NFES_QUALITY_CHECK_FAILED: "Fingerprint quality too low. Clean sensor and press firmly.",
        }
        _emit(
            {
                "ok": False,
                "error": hints.get(st, f"Enrollment status: {label}"),
                "status": label,
                "code": 408 if st == NFES_SCANNER_TIMEOUT else 500,
                "available_scanners": modules,
            }
        )
        lib.NffvUninitialize()
        return 1

    width = c_uint()
    height = c_uint()
    hres = c_float()
    vres = c_float()
    stride = ctypes.c_size_t()
    lib.NffvUserGetImage(
        h_user, byref(width), byref(height), byref(hres), byref(vres), byref(stride), None
    )
    w = int(width.value) or 500
    h = int(height.value) or 500
    s = int(stride.value) or w
    if s < w:
        s = w
    buf = (c_ubyte * (s * h))()
    img_result = lib.NffvUserGetImage(
        h_user, byref(width), byref(height), byref(hres), byref(vres), byref(stride), buf
    )
    if img_result != 0:
        _emit({"ok": False, "error": f"NffvUserGetImage failed: {err_msg(img_result)}", "code": 500})
        lib.NffvClearUsers()
        lib.NffvUninitialize()
        return 1

    w, h, s = int(width.value), int(height.value), int(stride.value)
    raw = bytes(buf)[: s * h]
    if s == w:
        image = Image.frombytes("L", (w, h), raw)
    else:
        packed = bytearray()
        for y in range(h):
            packed.extend(raw[y * s : y * s + w])
        image = Image.frombytes("L", (w, h), bytes(packed))

    small = image.resize((8, 8))
    pixels = list(small.getdata())
    avg = sum(pixels) / len(pixels)
    bits = "".join("1" if p >= avg else "0" for p in pixels)
    fp_hash = f"{int(bits, 2):016x}"

    png_buf = io.BytesIO()
    image.save(png_buf, format="PNG")
    image_data = "data:image/png;base64," + base64.b64encode(png_buf.getvalue()).decode("ascii")
    image.save(temp_dir / "last_capture.png")

    user_id = c_int()
    lib.NffvUserGetId(h_user, byref(user_id))
    lib.NffvClearUsers()
    lib.NffvUninitialize()

    _emit(
        {
            "ok": True,
            "fp_hash": fp_hash,
            "template_data": fp_hash,
            "image_data": image_data,
            "quality": None,
            "width": image.width,
            "height": image.height,
            "device_name": "Nffv Free Fingerprint Verification SDK",
            "nffv_user_id": int(user_id.value),
            "scanners": module_str,
            "error": None,
            "code": 200,
        }
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        _emit({"ok": False, "error": str(exc), "code": 500})
        raise SystemExit(1)
