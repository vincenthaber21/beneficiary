"""Secure database + media backup/restore helpers for e-BAHAGI."""
from __future__ import annotations

import json
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings
from django.db import connections

BACKUP_FORMAT = "ebahagi-backup-v1"
MAX_UPLOAD_BYTES = 512 * 1024 * 1024  # 512 MB
MAX_ZIP_MEMBERS = 50_000
MAX_UNCOMPRESSED_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB


class BackupError(Exception):
    """Raised when backup or restore fails validation or I/O."""


def _db_path() -> Path:
    return Path(settings.DATABASES["default"]["NAME"]).resolve()


def _media_root() -> Path:
    return Path(settings.MEDIA_ROOT).resolve()


def _close_db_connections() -> None:
    connections.close_all()


def create_sqlite_snapshot(dest: Path) -> None:
    """Create a consistent SQLite snapshot using the online backup API."""
    source = _db_path()
    if not source.exists():
        raise BackupError("Database file was not found.")

    dest.parent.mkdir(parents=True, exist_ok=True)
    src = sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True)
    try:
        dst = sqlite3.connect(str(dest))
        try:
            with dst:
                src.backup(dst)
        finally:
            dst.close()
    finally:
        src.close()


def build_backup_zip() -> tuple[bytes, str]:
    """Build an in-memory zip containing the DB, media files, and metadata."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"ebahagi_backup_{stamp}.zip"

    with tempfile.TemporaryDirectory(prefix="ebahagi_backup_") as tmp:
        tmp_path = Path(tmp)
        db_copy = tmp_path / "db.sqlite3"
        create_sqlite_snapshot(db_copy)

        media_root = _media_root()
        media_files: list[str] = []
        if media_root.exists():
            for path in media_root.rglob("*"):
                if path.is_file():
                    media_files.append(str(path.relative_to(media_root)).replace("\\", "/"))

        meta = {
            "format": BACKUP_FORMAT,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "app": "e-BAHAGI",
            "database": "sqlite3",
            "media_file_count": len(media_files),
        }

        zip_path = tmp_path / filename
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", json.dumps(meta, indent=2))
            zf.write(db_copy, arcname="db.sqlite3")
            if media_root.exists():
                for path in media_root.rglob("*"):
                    if path.is_file():
                        arc = Path("media") / path.relative_to(media_root)
                        zf.write(path, arcname=arc.as_posix())

        return zip_path.read_bytes(), filename


def _safe_member_path(name: str) -> Path | None:
    """Return a relative path if the zip member is allowed; else None."""
    cleaned = name.replace("\\", "/").strip("/")
    if not cleaned or cleaned.startswith("/") or ".." in cleaned.split("/"):
        return None
    if cleaned == "db.sqlite3" or cleaned == "manifest.json":
        return Path(cleaned)
    if cleaned.startswith("media/"):
        return Path(cleaned)
    return None


def _validate_zip(zf: zipfile.ZipFile) -> None:
    names = zf.namelist()
    if len(names) > MAX_ZIP_MEMBERS:
        raise BackupError("Backup archive has too many files.")

    total_uncompressed = 0
    has_db = False
    for info in zf.infolist():
        if info.is_dir():
            continue
        safe = _safe_member_path(info.filename)
        if safe is None:
            raise BackupError(f"Backup archive contains a disallowed path: {info.filename}")
        if safe.name == "db.sqlite3" and safe.parent == Path("."):
            has_db = True
        total_uncompressed += info.file_size
        if total_uncompressed > MAX_UNCOMPRESSED_BYTES:
            raise BackupError("Backup archive is too large when uncompressed.")

    if not has_db:
        raise BackupError("Backup archive is missing db.sqlite3.")


def _looks_like_sqlite(path: Path) -> bool:
    try:
        header = path.read_bytes()[:16]
    except OSError as exc:
        raise BackupError("Could not read uploaded database.") from exc
    return header.startswith(b"SQLite format 3\x00")


def restore_from_upload(uploaded_file) -> dict:
    """Restore database (and media when present) from an uploaded .zip or .sqlite3."""
    name = (getattr(uploaded_file, "name", "") or "").lower()
    size = getattr(uploaded_file, "size", None)
    if size is not None and size > MAX_UPLOAD_BYTES:
        raise BackupError("Uploaded file exceeds the maximum allowed size (512 MB).")

    with tempfile.TemporaryDirectory(prefix="ebahagi_restore_") as tmp:
        tmp_path = Path(tmp)
        incoming = tmp_path / "upload.bin"
        with incoming.open("wb") as out:
            for chunk in uploaded_file.chunks():
                out.write(chunk)
                if out.tell() > MAX_UPLOAD_BYTES:
                    raise BackupError("Uploaded file exceeds the maximum allowed size (512 MB).")

        restore_db = tmp_path / "db.sqlite3"
        restore_media = tmp_path / "media"
        media_count = 0
        manifest = {}

        if name.endswith(".zip") or zipfile.is_zipfile(incoming):
            with zipfile.ZipFile(incoming, "r") as zf:
                _validate_zip(zf)
                if "manifest.json" in zf.namelist():
                    try:
                        manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                        raise BackupError("Backup manifest.json is invalid.") from exc
                    if manifest.get("format") not in (None, BACKUP_FORMAT):
                        # Accept unknown format only if db.sqlite3 is valid.
                        pass

                for info in zf.infolist():
                    if info.is_dir():
                        continue
                    safe = _safe_member_path(info.filename)
                    if safe is None:
                        continue
                    target = tmp_path / safe
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(info, "r") as src, target.open("wb") as dst:
                        shutil.copyfileobj(src, dst)
                    if safe.as_posix().startswith("media/"):
                        media_count += 1

            if not restore_db.exists():
                raise BackupError("Backup archive is missing db.sqlite3.")
        elif name.endswith((".sqlite3", ".sqlite", ".db")):
            shutil.copy2(incoming, restore_db)
        else:
            raise BackupError("Upload a .zip backup or a .sqlite3 database file.")

        if not _looks_like_sqlite(restore_db):
            raise BackupError("Uploaded file is not a valid SQLite database.")

        # Quick integrity check
        conn = sqlite3.connect(str(restore_db))
        try:
            row = conn.execute("PRAGMA integrity_check;").fetchone()
            if not row or row[0] != "ok":
                raise BackupError("SQLite integrity check failed for the uploaded database.")
        finally:
            conn.close()

        db_path = _db_path()
        media_root = _media_root()
        backup_before = tmp_path / "pre_restore_db.sqlite3"

        _close_db_connections()

        if db_path.exists():
            shutil.copy2(db_path, backup_before)

        try:
            db_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(restore_db, db_path)

            if restore_media.exists() and restore_media.is_dir():
                if media_root.exists():
                    shutil.rmtree(media_root)
                shutil.copytree(restore_media, media_root)
        except Exception as exc:
            # Best-effort rollback of the database file
            if backup_before.exists():
                try:
                    shutil.copy2(backup_before, db_path)
                except OSError:
                    pass
            raise BackupError(f"Restore failed: {exc}") from exc
        finally:
            _close_db_connections()

        return {
            "media_files_restored": media_count,
            "manifest": manifest,
            "database": str(db_path),
        }
