"""
Auto-start the local fingerprint HTTP bridge when Django runserver starts.

Keeps a single process on 127.0.0.1:8765 so you do not need a second terminal.
Skips launch if the port is already in use (no duplicate bridges).

FPModule_SDK.dll is 32-bit, so the bridge is launched with 32-bit Python
(py -3.11-32 / py -3-32), matching start_bridge.bat.
"""

from __future__ import annotations

import os
import shutil
import socket
import struct
import subprocess
import sys
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8765


def _bridge_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "fingerprint_bridge"


def _port_open(host: str = HOST, port: int = PORT) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.4):
            return True
    except OSError:
        return False


def _should_autostart() -> bool:
    """Start only for runserver, once (not the autoreload parent watcher)."""
    if os.environ.get("FINGERPRINT_BRIDGE_AUTOSTART", "1").strip().lower() in (
        "0",
        "false",
        "no",
        "off",
    ):
        return False
    if "runserver" not in sys.argv:
        return False
    # Autoreload parent has RUN_MAIN unset; the child sets RUN_MAIN=true.
    # With --noreload there is a single process and RUN_MAIN stays unset.
    if "--noreload" in sys.argv:
        return True
    return os.environ.get("RUN_MAIN") == "true"


def _python_is_32bit(cmd: list[str]) -> bool:
    try:
        proc = subprocess.run(
            [*cmd, "-c", "import struct; print(struct.calcsize('P') * 8)"],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0 and proc.stdout.strip() == "32"


def _bridge_python_cmd() -> list[str]:
    """Prefer 32-bit Python for Hikvision FPModule_SDK.dll."""
    override = os.environ.get("FINGERPRINT_BRIDGE_PYTHON", "").strip()
    if override:
        return override.split()

    if sys.platform == "win32" and shutil.which("py"):
        for args in (["py", "-3.11-32"], ["py", "-3-32"]):
            if _python_is_32bit(args):
                return args

    # Fall back to current interpreter only if it is already 32-bit.
    if struct.calcsize("P") * 8 == 32:
        return [sys.executable]

    raise RuntimeError(
        "FPModule_SDK.dll is 32-bit, but no 32-bit Python was found. "
        "Install Python 3.11 32-bit and use: py -3.11-32 app.py "
        "(or run fingerprint_bridge/start_bridge.bat). "
        "Or set FINGERPRINT_BRIDGE_PYTHON to a 32-bit interpreter."
    )


def ensure_fingerprint_bridge() -> None:
    """Launch fingerprint_bridge/app.py if it is not already listening."""
    if not _should_autostart():
        return

    if _port_open():
        print(f"Fingerprint bridge already running on http://{HOST}:{PORT}")
        return

    app_path = _bridge_dir() / "app.py"
    if not app_path.is_file():
        print(f"Fingerprint bridge not found at {app_path}")
        return

    try:
        py_cmd = _bridge_python_cmd()
    except RuntimeError as exc:
        print(f"Could not start fingerprint bridge: {exc}")
        return

    creationflags = 0
    if sys.platform == "win32":
        # Own process group so Ctrl+C on Django does not kill the bridge mid-scan;
        # next runserver reuses it if still listening.
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

    try:
        proc = subprocess.Popen(
            [*py_cmd, str(app_path)],
            cwd=str(_bridge_dir()),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
        )
    except OSError as exc:
        print(f"Could not start fingerprint bridge: {exc}")
        return

    print(
        f"Fingerprint bridge started (pid {proc.pid}) via {' '.join(py_cmd)} "
        f"on http://{HOST}:{PORT}"
    )
