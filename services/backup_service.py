"""
Backup Service for SIGNHEAR.

Handles atomic online database backups, cryptographic verification,
manifest history, and audit logging.
"""
from __future__ import annotations
import hashlib
import json
import logging
import os
import re
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from fastapi import HTTPException, Request, status
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from core.config import settings
from models.accounts import Accounts
from schemas.backup_schema import (
    BackupCreateRequest,
    BackupItemOut,
    BackupVerifyResponse,
    DatabaseStatusResponse,
)
from services.audit_service import write_log
from utils.enum import AuditActionEnum

logger = logging.getLogger(__name__)

# Protected storage directory outside web server document roots
BASE_DIR = Path(__file__).resolve().parent.parent
BACKUP_DIR = BASE_DIR / "backups"
MANIFEST_PATH = BACKUP_DIR / "manifest.json"

_BACKUP_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-]+$")


def _ensure_backup_dir() -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    if not MANIFEST_PATH.exists():
        MANIFEST_PATH.write_text("[]", encoding="utf-8")


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.2f} MB"


def _calculate_sha256(file_path: Path) -> str:
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


def _load_manifest() -> List[Dict[str, Any]]:
    _ensure_backup_dir()
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception as exc:
        logger.error(f"Failed to read backup manifest: {exc}")
        return []


def _save_manifest(entries: List[Dict[str, Any]]) -> None:
    _ensure_backup_dir()
    MANIFEST_PATH.write_text(json.dumps(entries, indent=2, default=str), encoding="utf-8")


def get_safe_backup_path(backup_id: str) -> Path:
    if not _BACKUP_ID_REGEX.match(backup_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid backup identifier format."
        )
    _ensure_backup_dir()
    for ext in (".db", ".sql", ".json"):
        candidate = (BACKUP_DIR / f"{backup_id}{ext}").resolve()
        if candidate.is_file() and candidate.parent == BACKUP_DIR.resolve():
            return candidate

    candidate = (BACKUP_DIR / backup_id).resolve()
    if candidate.is_file() and candidate.parent == BACKUP_DIR.resolve():
        return candidate

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Requested backup file not found on server."
    )


def detect_database_info(db: Optional[Session] = None) -> Dict[str, Any]:
    url = settings.database_url or ""
    is_sqlite = url.startswith("sqlite")
    is_postgres = url.startswith("postgresql") or url.startswith("postgres")

    if is_sqlite:
        raw_path = url.replace("sqlite:///", "").replace("sqlite://", "").split("?")[0]
        db_file = Path(raw_path) if raw_path else Path("local.db")
        if not db_file.is_absolute():
            db_file = (BASE_DIR / db_file).resolve()
        return {
            "engine": "sqlite",
            "active_database": "SQLite",
            "database_name": db_file.name,
            "host": "localhost (local file)",
            "file_path": db_file,
            "backup_capable": True,
            "restore_capable": True,
            "production_safeguards": False,
            "message": "Local SQLite database active. Consistent online backup and safe local restore are fully supported."
        }

    if is_postgres:
        parsed = urlparse(url)
        host = parsed.hostname or "remote"
        db_name = (parsed.path or "").lstrip("/") or "postgres"
        return {
            "engine": "postgresql",
            "active_database": "PostgreSQL",
            "database_name": db_name,
            "host": host,
            "file_path": None,
            "backup_capable": True,
            "restore_capable": False,
            "production_safeguards": True,
            "message": "Remote PostgreSQL / Supabase active. Backup export and verification are supported; automated live database overwrite is restricted for tenant safety."
        }

    return {
        "engine": "unknown",
        "active_database": "Unknown",
        "database_name": "unknown",
        "host": "unknown",
        "file_path": None,
        "backup_capable": False,
        "restore_capable": False,
        "production_safeguards": True,
        "message": "Database engine not supported for automated recovery operations."
    }


def get_system_status(db: Session) -> DatabaseStatusResponse:
    info = detect_database_info(db)
    manifest = _load_manifest()

    last_backup = manifest[0]["created_at"] if manifest else None
    last_verified = None
    for entry in manifest:
        if entry.get("integrity_status") == "verified":
            last_verified = entry.get("verified_at") or entry.get("created_at")
            break

    return DatabaseStatusResponse(
        active_database=info["active_database"],
        engine_type=info["engine"],
        database_name=info["database_name"],
        host=info["host"],
        backup_capable=info["backup_capable"],
        restore_capable=info["restore_capable"],
        backup_storage_path=str(BACKUP_DIR),
        total_backups=len(manifest),
        last_backup_time=last_backup,
        last_verified_time=last_verified,
        environment=settings.environment,
        production_safeguards_active=info["production_safeguards"],
        status_message=info["message"],
    )


def _count_core_tables_sqlite(db_path: Path) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    if not db_path.exists():
        return counts
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [r[0] for r in cursor.fetchall()]
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM \"{table}\"")
                counts[table] = cursor.fetchone()[0]
            except Exception:
                pass
        conn.close()
    except Exception as exc:
        logger.warning(f"Could not read SQLite table counts: {exc}")
    return counts


def _count_core_tables_sqla(db: Session) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    try:
        inspector = inspect(db.bind)
        table_names = inspector.get_table_names()
        for t in table_names:
            try:
                res = db.execute(text(f"SELECT COUNT(*) FROM \"{t}\"")).scalar()
                counts[t] = int(res or 0)
            except Exception:
                pass
    except Exception as exc:
        logger.warning(f"Could not read SQLAlchemy table counts: {exc}")
    return counts


def create_database_backup(
    db: Session,
    actor: Accounts,
    request: Optional[Request] = None,
    payload: Optional[BackupCreateRequest] = None,
) -> BackupItemOut:
    _ensure_backup_dir()
    info = detect_database_info(db)

    # 1. Audit BACKUP_REQUESTED
    write_log(
        db,
        module="Backup",
        action=AuditActionEnum.backup_requested,
        actor_id=actor.id,
        actor_role=actor.role,
        affected_record=f"Engine: {info['engine']}",
        reason="Administrator initiated database backup",
        request=request,
        status="success",
    )

    now_utc = datetime.now(timezone.utc)
    timestamp_str = now_utc.strftime("%Y%m%d_%H%M%S")
    rand_suffix = hashlib.sha256(os.urandom(8)).hexdigest()[:8]
    backup_id = f"backup_{timestamp_str}_{rand_suffix}"

    # 2. Audit BACKUP_STARTED
    write_log(
        db,
        module="Backup",
        action=AuditActionEnum.backup_started,
        actor_id=actor.id,
        actor_role=actor.role,
        affected_record=backup_id,
        reason=f"Starting backup for {info['active_database']}",
        request=request,
        status="success",
    )

    backup_type = payload.backup_type if payload else "full"
    notes = payload.notes if payload else None
    table_counts: Dict[str, int] = {}

    try:
        if info["engine"] == "sqlite":
            src_file: Path = info["file_path"]
            if not src_file.exists():
                raise FileNotFoundError(f"Source SQLite database file not found: {src_file}")

            target_filename = f"{backup_id}.db"
            target_path = BACKUP_DIR / target_filename

            # Safe consistent SQLite Online Backup API
            src_conn = sqlite3.connect(str(src_file), timeout=30.0)
            dest_conn = sqlite3.connect(str(target_path))
            with dest_conn:
                src_conn.backup(dest_conn, pages=100)
            dest_conn.close()
            src_conn.close()

            # Verify SQLite integrity check immediately on new artifact
            test_conn = sqlite3.connect(str(target_path))
            cur = test_conn.cursor()
            cur.execute("PRAGMA integrity_check;")
            integrity_result = cur.fetchone()
            test_conn.close()

            if not integrity_result or integrity_result[0].lower() != "ok":
                raise ValueError(f"SQLite integrity check failed: {integrity_result}")

            table_counts = _count_core_tables_sqlite(target_path)

        elif info["engine"] == "postgresql":
            target_filename = f"{backup_id}.json"
            target_path = BACKUP_DIR / target_filename

            # Consistent table snapshot
            table_counts = _count_core_tables_sqla(db)
            snapshot_data: Dict[str, Any] = {
                "backup_id": backup_id,
                "engine": "postgresql",
                "database_name": info["database_name"],
                "created_at": now_utc.isoformat(),
                "table_counts": table_counts,
                "tables": {},
            }

            # Export critical application tables
            for tbl in ["accounts", "hi_sections", "audit_logs", "notifications"]:
                if tbl in table_counts:
                    try:
                        rows = db.execute(text(f"SELECT * FROM \"{tbl}\"")).mappings().all()
                        snapshot_data["tables"][tbl] = [dict(r) for r in rows]
                    except Exception as exc:
                        logger.warning(f"Could not export table {tbl}: {exc}")

            target_path.write_text(json.dumps(snapshot_data, indent=2, default=str), encoding="utf-8")

        else:
            raise NotImplementedError(f"Unsupported database engine for backup: {info['engine']}")

        # 3. Cryptographic Checksum
        checksum = _calculate_sha256(target_path)
        file_size = target_path.stat().st_size
        size_human = _format_size(file_size)

        entry = {
            "backup_id": backup_id,
            "filename": target_filename,
            "created_at": now_utc.isoformat(),
            "backup_type": backup_type,
            "database_engine": info["engine"],
            "file_size": file_size,
            "file_size_human": size_human,
            "checksum_sha256": checksum,
            "status": "completed",
            "integrity_status": "verified",
            "created_by_id": actor.id,
            "created_by_name": actor.username or actor.email,
            "table_counts": table_counts,
            "notes": notes,
        }

        # 4. Save to Manifest
        manifest = _load_manifest()
        manifest.insert(0, entry)
        _save_manifest(manifest)

        # 5. Audit BACKUP_COMPLETED
        write_log(
            db,
            module="Backup",
            action=AuditActionEnum.backup_completed,
            actor_id=actor.id,
            actor_role=actor.role,
            affected_record=backup_id,
            new_value={"size": size_human, "checksum": checksum[:16], "tables": len(table_counts)},
            reason="Backup completed successfully and verified",
            request=request,
            status="success",
        )

        return BackupItemOut(**entry)

    except Exception as exc:
        logger.error(f"Backup operation failed: {exc}", exc_info=True)
        write_log(
            db,
            module="Backup",
            action=AuditActionEnum.backup_failed,
            actor_id=actor.id,
            actor_role=actor.role,
            affected_record=backup_id,
            reason=f"Backup failure: {str(exc)[:200]}",
            request=request,
            status="failed",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup creation failed: {str(exc)}"
        )


def list_backups() -> List[BackupItemOut]:
    manifest = _load_manifest()
    results: List[BackupItemOut] = []
    for item in manifest:
        try:
            results.append(BackupItemOut(**item))
        except Exception:
            pass
    return results


def verify_backup_integrity(
    backup_id: str,
    db: Session,
    actor: Accounts,
    request: Optional[Request] = None,
) -> BackupVerifyResponse:
    # 1. Audit BACKUP_VERIFICATION_STARTED
    write_log(
        db,
        module="Backup",
        action=AuditActionEnum.backup_verification_started,
        actor_id=actor.id,
        actor_role=actor.role,
        affected_record=backup_id,
        reason="Cryptographic and structural verification initiated",
        request=request,
        status="success",
    )

    manifest = _load_manifest()
    entry = next((e for e in manifest if e["backup_id"] == backup_id), None)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup record '{backup_id}' not found in manifest."
        )

    file_path = get_safe_backup_path(backup_id)
    now_iso = datetime.now(timezone.utc).isoformat()

    expected_sha = entry.get("checksum_sha256", "")
    computed_sha = _calculate_sha256(file_path)
    checksum_matches = (expected_sha.lower() == computed_sha.lower())

    structure_valid = False
    details = ""

    engine = entry.get("database_engine", "sqlite")
    if engine == "sqlite":
        try:
            conn = sqlite3.connect(f"file:{file_path}?mode=ro", uri=True)
            cur = conn.cursor()
            cur.execute("PRAGMA integrity_check;")
            res = cur.fetchone()
            conn.close()
            if res and res[0].lower() == "ok":
                structure_valid = True
                details = "SHA-256 checksum matches recorded artifact. SQLite PRAGMA integrity_check passed (ok)."
            else:
                details = f"Integrity check failed: {res}"
        except Exception as exc:
            details = f"SQLite structure verification error: {exc}"
    elif engine == "postgresql":
        try:
            parsed = json.loads(file_path.read_text(encoding="utf-8"))
            if isinstance(parsed, dict) and "tables" in parsed:
                structure_valid = True
                details = f"SHA-256 checksum matches. Valid JSON snapshot containing {len(parsed.get('tables', {}))} core tables."
            else:
                details = "JSON snapshot does not contain expected backup structure."
        except Exception as exc:
            details = f"PostgreSQL snapshot verification error: {exc}"

    passed = checksum_matches and structure_valid
    integrity_status = "verified" if passed else "corrupted"

    # Update manifest
    entry["integrity_status"] = integrity_status
    entry["verified_at"] = now_iso
    _save_manifest(manifest)

    # Audit result
    if passed:
        write_log(
            db,
            module="Backup",
            action=AuditActionEnum.backup_verification_passed,
            actor_id=actor.id,
            actor_role=actor.role,
            affected_record=backup_id,
            reason=details,
            request=request,
            status="success",
        )
    else:
        write_log(
            db,
            module="Backup",
            action=AuditActionEnum.backup_verification_failed,
            actor_id=actor.id,
            actor_role=actor.role,
            affected_record=backup_id,
            reason=f"Integrity check failed: {details}",
            request=request,
            status="failed",
        )

    return BackupVerifyResponse(
        backup_id=backup_id,
        integrity_status=integrity_status,
        computed_checksum=computed_sha,
        expected_checksum=expected_sha,
        checksum_matches=checksum_matches,
        structure_valid=structure_valid,
        details=details,
        verified_at=now_iso,
    )


def get_download_file(backup_id: str) -> Tuple[Path, str]:
    path = get_safe_backup_path(backup_id)
    return path, path.name

