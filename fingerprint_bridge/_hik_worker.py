"""Child process that drives Hikvision FPModule_SDK.dll (DS-K1F820-F)."""

from __future__ import annotations

import base64
import io
import json
import os
import struct
import sys
import time
from ctypes import CDLL, POINTER, WinDLL, byref, c_int, c_long, c_ubyte
from pathlib import Path


def _emit(payload: dict):
    print(json.dumps(payload), flush=True)


def _pe_machine(dll_path: Path) -> str | None:
    """Return 'x86', 'x64', or None if not a PE file."""
    try:
        data = dll_path.read_bytes()[:4096]
        if data[:2] != b"MZ":
            return None
        e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
        if data[e_lfanew : e_lfanew + 4] != b"PE\0\0":
            return None
        machine = struct.unpack_from("<H", data, e_lfanew + 4)[0]
        if machine == 0x14C:
            return "x86"
        if machine == 0x8664:
            return "x64"
    except Exception:
        return None
    return None


def _load_lib(dll_path: Path):
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(str(dll_path.parent))
    os.environ["PATH"] = str(dll_path.parent) + os.pathsep + os.environ.get("PATH", "")
    last_err = None
    for loader in (WinDLL, CDLL):
        try:
            return loader(str(dll_path))
        except OSError as exc:
            last_err = exc
    raise OSError(str(last_err) if last_err else f"Failed to load {dll_path}")


def _ahash_hex(image) -> str:
    small = image.resize((8, 8))
    pixels = list(small.getdata())
    avg = sum(pixels) / len(pixels)
    bits = "".join("1" if p >= avg else "0" for p in pixels)
    return f"{int(bits, 2):016x}"


def main() -> int:
    lib_dir = Path(os.environ.get("HIK_LIB_DIR") or os.environ.get("NFFV_LIB_DIR") or ".")
    action = os.environ.get("HIK_ACTION") or os.environ.get("NFFV_ACTION") or "status"
    timeout_sec = float(os.environ.get("HIK_TIMEOUT") or os.environ.get("NFFV_TIMEOUT") or "25")
    temp_dir = Path(os.environ.get("HIK_TEMP") or os.environ.get("NFFV_TEMP") or ".")
    temp_dir.mkdir(parents=True, exist_ok=True)

    dll_path = lib_dir / "FPModule_SDK.dll"
    if not dll_path.exists():
        # also accept nested hikvision folder
        alt = lib_dir / "hikvision" / "FPModule_SDK.dll"
        dll_path = alt if alt.exists() else dll_path

    if not dll_path.exists():
        _emit(
            {
                "ok": False,
                "backend": "hikvision",
                "error": (
                    f"Missing {lib_dir / 'FPModule_SDK.dll'}. "
                    "Copy Hikvision Fingerprint Module SDK (FPModule_SDK.dll) into "
                    "fingerprint_bridge/lib/ for DS-K1F820-F support."
                ),
                "code": 503,
            }
        )
        return 1

    pe = _pe_machine(dll_path)
    py_bits = struct.calcsize("P") * 8
    if pe == "x86" and py_bits == 64:
        _emit(
            {
                "ok": False,
                "backend": "hikvision",
                "error": (
                    "FPModule_SDK.dll is 32-bit, but this Python is 64-bit. "
                    "Use the 32-bit runtime we installed:  py -3.11-32 app.py"
                    "  (or run start_bridge.bat)."
                ),
                "code": 503,
                "dll": str(dll_path),
                "dll_arch": pe,
                "python_bits": py_bits,
            }
        )
        return 1
    if pe == "x64" and py_bits == 32:
        _emit(
            {
                "ok": False,
                "backend": "hikvision",
                "error": (
                    "FPModule_SDK.dll is 64-bit, but this Python is 32-bit. "
                    "Use 64-bit Python to load it."
                ),
                "code": 503,
                "dll": str(dll_path),
                "dll_arch": pe,
                "python_bits": py_bits,
            }
        )
        return 1

    try:
        lib = _load_lib(dll_path)
    except OSError as exc:
        _emit(
            {
                "ok": False,
                "backend": "hikvision",
                "error": f"Failed to load FPModule_SDK.dll: {exc}",
                "code": 503,
                "dll": str(dll_path),
                "dll_arch": pe,
                "python_bits": py_bits,
            }
        )
        return 1

    lib.FPModule_OpenDevice.restype = c_int
    lib.FPModule_CloseDevice.restype = c_int
    lib.FPModule_DetectFinger.argtypes = [POINTER(c_long)]
    lib.FPModule_DetectFinger.restype = c_int
    lib.FPModule_CaptureImage.argtypes = [POINTER(c_ubyte), POINTER(c_int), POINTER(c_int)]
    lib.FPModule_CaptureImage.restype = c_int
    try:
        lib.FPModule_GetSDKVersion.argtypes = [POINTER(c_ubyte)]
        lib.FPModule_GetSDKVersion.restype = c_int
        lib.FPModule_GetDeviceInfo.argtypes = [POINTER(c_ubyte)]
        lib.FPModule_GetDeviceInfo.restype = c_int
    except Exception:
        pass

    def sdk_version() -> str:
        try:
            buf = (c_ubyte * 64)()
            lib.FPModule_GetSDKVersion(buf)
            return bytes(buf).split(b"\0", 1)[0].decode("ascii", errors="ignore")
        except Exception:
            return ""

    def device_info() -> str:
        try:
            buf = (c_ubyte * 64)()
            lib.FPModule_GetDeviceInfo(buf)
            return bytes(buf).split(b"\0", 1)[0].decode("ascii", errors="ignore")
        except Exception:
            return ""

    if lib.FPModule_OpenDevice() != 0:
        _emit(
            {
                "ok": False,
                "backend": "hikvision",
                "error": (
                    "Unable to open Hikvision fingerprint device. "
                    "Check USB connection: Device Manager should show the recorder "
                    "(not 'Unknown USB Device / Device Descriptor Request Failed'). "
                    "Try another USB port/cable, then replug the DS-K1F820-F."
                ),
                "code": 503,
                "sdk_version": sdk_version(),
                "dll": str(dll_path),
            }
        )
        return 1

    try:
        if action == "status":
            _emit(
                {
                    "ok": True,
                    "backend": "hikvision",
                    "initialized": True,
                    "device_name": "Hikvision DS-K1F820-F",
                    "device_info": device_info() or None,
                    "sdk_version": sdk_version() or None,
                    "available_scanners": ["Hikvision DS-K1F820-F"],
                    "error": None,
                }
            )
            return 0

        # capture: wait for finger, then grab image
        deadline = time.time() + max(1.0, timeout_sec)
        detected = False
        while time.time() < deadline:
            status = c_long(0)
            rc = lib.FPModule_DetectFinger(byref(status))
            if rc == 0 and int(status.value) == 1:
                detected = True
                break
            time.sleep(0.15)

        if not detected:
            _emit(
                {
                    "ok": False,
                    "backend": "hikvision",
                    "error": "No finger detected in time. Place finger firmly on the DS-K1F820-F and retry.",
                    "code": 408,
                }
            )
            return 1

        # DS-K1F820-F native size is 256x288; allocate generous buffer
        max_w, max_h = 512, 512
        img_buf = (c_ubyte * (max_w * max_h))()
        width = c_int(0)
        height = c_int(0)
        rc = lib.FPModule_CaptureImage(img_buf, byref(width), byref(height))
        w, h = int(width.value), int(height.value)
        if rc != 0 or w <= 0 or h <= 0 or w * h > max_w * max_h:
            _emit(
                {
                    "ok": False,
                    "backend": "hikvision",
                    "error": f"FPModule_CaptureImage failed (rc={rc}, size={w}x{h}).",
                    "code": 500,
                }
            )
            return 1

        from PIL import Image

        raw = bytes(img_buf)[: w * h]
        image = Image.frombytes("L", (w, h), raw)
        fp_hash = _ahash_hex(image)

        png_buf = io.BytesIO()
        image.save(png_buf, format="PNG")
        image_data = "data:image/png;base64," + base64.b64encode(png_buf.getvalue()).decode("ascii")
        image.save(temp_dir / "last_capture.png")

        _emit(
            {
                "ok": True,
                "backend": "hikvision",
                "fp_hash": fp_hash,
                "template_data": fp_hash,
                "image_data": image_data,
                "quality": None,
                "width": w,
                "height": h,
                "device_name": "Hikvision DS-K1F820-F",
                "sdk_version": sdk_version() or None,
                "error": None,
                "code": 200,
            }
        )
        return 0
    finally:
        try:
            lib.FPModule_CloseDevice()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        _emit({"ok": False, "backend": "hikvision", "error": str(exc), "code": 500})
        raise SystemExit(1)
