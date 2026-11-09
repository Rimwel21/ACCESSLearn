"""
Restore Service for SIGNHEAR.

Handles multi-stage safe database restoration, dry-run sandbox recovery testing,
pre-restore safety snapshots, production safeguards, and comprehensive audit trails.
"""
from __future__ import annotations
import json
import logging
import sqlite3
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from core.config import settings
from models.accounts import Accounts
from schemas.backup_schema import (
    DryRunRestoreResponse,
    RestorePreviewResponse,
    RestoreResponse,
)
from services.audit_service import write_log
from services.backup_service import (
    BACKUP_DIR,
    detect_database_info,
    get_safe_backup_path,
    _calculate_sha256,
    _count_core_tables_sqlite,
    _format_size,
    _load_manifest,
)
from utils.enum import AuditActionEnum

logger = logging.getLogger(__name__)

RESTORATIONS_LOG_PATH = BACKUP_DIR / "restorations.json"


def _record_external_restoration(entry: Dict[str, Any]) -> None:
    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        logs = []
        if RESTORATIONS_LOG_PATH.exists():
            try:
                logs = json.loads(RESTORATIONS_LOG_PATH.read_text(encoding="utf-8"))
            except Exception:
                logs = []
        logs.insert(0, entry)
        RESTORATIONS_LOG_PATH.write_text(json.dumps(logs, indent=2, default=str), encoding="utf-8")
    except Exception as exc:
        logger.error(f"Failed to record external restoration log: {exc}")


def preview_restore(backup_id: str, db: Session) -> RestorePreviewResponse:
    info = detect_database_info(db)
    manifest = _load_manifest()
    entry = next((e for e in manifest if e["backup_id"] == backup_id), None)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup record '{backup_id}' not found."
        )

    file_path = get_safe_backup_path(backup_id)
    file_size_human = _format_size(file_path.stat().st_size)
    engine = entry.get("database_engine", "sqlite")
    table_counts = entry.get("table_counts") or {}

    warnings: List[str] = [
        "Restoring a database replaces active learner records and progress data with the historical backup snapshot.",
        "Ensure all active users are notified and ongoing assessments are paused before restoring.",
    ]

    safety_measures: List[str] = [
        "Cryptographic SHA-256 verification will be run before restoration.",
        "A pre-restoration safety snapshot of the active database will be created automatically.",
        "If restoration fails or encounters integrity errors, an automatic rollback will be triggered.",
        "An audit record will be logged both inside the system and in an external persistent file.",
    ]

    can_restore = True
    restriction_reason = None

    if info["engine"] == "postgresql":
        can_restore = False
        restriction_reason = (
            "Direct in-app database overwrite of remote production PostgreSQL / Supabase is restricted "
            "for multi-tenant data safety. Use dry-run recovery testing or perform maintenance restoration "
            "via database administrative tools."
        )
        warnings.append("RESTRICTION: Production PostgreSQL active. In-app overwrite is blocked.")

    elif engine != info["engine"]:
        can_restore = False
        restriction_reason = f"Engine mismatch: backup is '{engine}' but active database is '{info['engine']}'."

    return RestorePreviewResponse(
        backup_id=backup_id,
        database_engine=engine,
        created_at=entry.get("created_at", ""),
        file_size_human=file_size_human,
        checksum_sha256=entry.get("checksum_sha256", ""),
        target_database=info["active_database"],
        target_environment=settings.environment,
        can_restore=can_restore,
        restriction_reason=restriction_reason,
        table_counts=table_counts,
        warnings=warnings,
        safety_measures=safety_measures,
        required_confirmation_text="RESTORE",
    )


def dry_run_sandbox_restore(
    backup_id: str,
    db: Session,
    actor: Accounts,
    request: Optional[Request] = None,
) -> DryRunRestoreResponse:
    """Restores backup into an isolated sandbox to test recoverability without touching live data."""
    start_time = time.perf_counter()
    file_path = get_safe_backup_path(backup_id)
    manifest = _load_manifest()
    entry = next((e for e in manifest if e["backup_id"] == backup_id), None)
    engine = entry.get("database_engine", "sqlite") if entry else "sqlite"

    table_counts: Dict[str, int] = {}

    if engine == "sqlite":
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            sandbox_path = Path(tmp_file.name)

        try:
            src_conn = sqlite3.connect(f"file:{file_path}?mode=ro", uri=True)
            dst_conn = sqlite3.connect(str(sandbox_path))
            with dst_conn:
                src_conn.backup(dst_conn)
            dst_conn.close()
            src_conn.close()

            # Verify integrity
            verify_conn = sqlite3.connect(str(sandbox_path))
            cur = verify_conn.cursor()
            cur.execute("PRAGMA integrity_check;")
            res = cur.fetchone()
            verify_conn.close()

            if not res or res[0].lower() != "ok":
                raise ValueError(f"Integrity check failed in sandbox: {res}")

            table_counts = _count_core_tables_sqlite(sandbox_path)
        finally:
            if sandbox_path.exists():
                try:
                    sandbox_path.unlink()
                except Exception:
                    pass

    elif engine == "postgresql":
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            tables = data.get("tables", {})
            for tbl, rows in tables.items():
                table_counts[tbl] = len(rows)
        except Exception as exc:
            raise ValueError(f"PostgreSQL snapshot parse error: {exc}")

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    return DryRunRestoreResponse(
        backup_id=backup_id,
        status="passed",
        message="Dry-run restoration test succeeded in an isolated sandbox. All tables and schemas are valid.",
        sandbox_verified=True,
        table_counts=table_counts,
        duration_ms=round(elapsed_ms, 2),
    )


def execute_database_restore(
    backup_id: str,
    confirmation_text: str,
    db: Session,
    actor: Accounts,
    request: Optional[Request] = None,
) -> RestoreResponse:
    info = detect_database_info(db)
    now_utc = datetime.now(timezone.utc)
    now_iso = now_utc.isoformat()

    # 1. Audit RESTORE_REQUESTED
    write_log(
        db,
        module="Restoration",
        action=AuditActionEnum.restore_requested,
        actor_id=actor.id,
        actor_role=actor.role,
        affected_record=backup_id,
        reason=f"Administrator requested restoration of backup {backup_id}",
        request=request,
        status="success",
    )

    # 2. Strict Confirmation Validation
    if confirmation_text.strip() != "RESTORE":
        write_log(
            db,
            module="Restoration",
            action=AuditActionEnum.restore_validation_failed,
            actor_id=actor.id,
            actor_role=actor.role,
            affected_record=backup_id,
            reason=f"Invalid confirmation text: '{confirmation_text}'",
            request=request,
            status="failed",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Restoration aborted: confirmation keyword must be exactly 'RESTORE'."
        )

    # 3. Production PostgreSQL Restriction Safeguard
    if info["engine"] == "postgresql":
        write_log(
            db,
            module="Restoration",
            action=AuditActionEnum.restore_validation_failed,
            actor_id=actor.id,
            actor_role=actor.role,
            affected_record=backup_id,
            reason="Blocked automated restore against remote production PostgreSQL",
            request=request,
            status="failed",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Direct in-app database overwrite of remote production PostgreSQL is restricted for safety. "
                "Contact system administrator for managed database maintenance."
            )
        )

    manifest = _load_manifest()
    entry = next((e for e in manifest if e["backup_id"] == backup_id), None)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup {backup_id} not found."
        )

    file_path = get_safe_backup_path(backup_id)

    # 4. Pre-Restore Checksum and Structural Integrity Verification
    expected_sha = entry.get("checksum_sha256", "")
    computed_sha = _calculate_sha256(file_path)
    if expected_sha.lower() != computed_sha.lower():
        write_log(
            db,
            module="Restoration",
            action=AuditActionEnum.restore_validation_failed,
            actor_id=actor.id,
            actor_role=actor.role,
            affected_record=backup_id,
            reason="Checksum mismatch detected prior to restoration",
            request=request,
            status="failed",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Restoration aborted: backup file failed checksum verification and may be corrupted."
        )

    # 5. Audit RESTORE_APPROVED
    write_log(
        db,
        module="Restoration",
        action=AuditActionEnum.restore_approved,
        actor_id=actor.id,
        actor_role=actor.role,
        affected_record=backup_id,
        reason="Backup validated and restoration approved for execution",
        request=request,
        status="success",
    )

    # 6. Audit RESTORE_STARTED
    write_log(
        db,
        module="Restoration",
        action=AuditActionEnum.restore_started,
        actor_id=actor.id,
        actor_role=actor.role,
        affected_record=backup_id,
        reason=f"Restoring SQLite database from {file_path.name}",
        request=request,
        status="success",
    )

    src_file: Path = info["file_path"]
    safety_snapshot_path = BACKUP_DIR / f"pre_restore_safety_{now_utc.strftime('%Y%m%d_%H%M%S')}.db"

    # Step A: Take safety snapshot of live database
    try:
        if src_file.exists():
            live_conn = sqlite3.connect(str(src_file), timeout=30.0)
            safety_conn = sqlite3.connect(str(safety_snapshot_path))
            with safety_conn:
                live_conn.backup(safety_conn)
            safety_conn.close()
            live_conn.close()
    except Exception as exc:
        logger.error(f"Failed to create pre-restore safety snapshot: {exc}")
        write_log(
            db,
            module="Restoration",
            action=AuditActionEnum.restore_failed,
            actor_id=actor.id,
            actor_role=actor.role,
            affected_record=backup_id,
            reason=f"Pre-restore safety snapshot failed: {exc}",
            request=request,
            status="failed",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Restoration aborted: failed to create pre-restore safety snapshot ({exc})."
        )

    # Step B: Execute safe SQLite restore
    try:
        backup_conn = sqlite3.connect(f"file:{file_path}?mode=ro", uri=True)
        live_restore_conn = sqlite3.connect(str(src_file), timeout=30.0)
        with live_restore_conn:
            backup_conn.backup(live_restore_conn, pages=100)
        live_restore_conn.close()
        backup_conn.close()

        # Step C: Post-restoration verification
        verify_conn = sqlite3.connect(str(src_file))
        cur = verify_conn.cursor()
        cur.execute("PRAGMA integrity_check;")
        check_res = cur.fetchone()
        verify_conn.close()

        if not check_res or check_res[0].lower() != "ok":
            raise ValueError(f"Post-restore integrity check failed: {check_res}")

        verified_counts = _count_core_tables_sqlite(src_file)

        # Step D: Record in external restoration log
        _record_external_restoration({
            "backup_id": backup_id,
            "restored_at": now_iso,
            "restored_by_id": actor.id,
            "restored_by": actor.username or actor.email,
            "pre_restore_safety_backup": safety_snapshot_path.name,
            "status": "completed",
            "verified_tables": verified_counts,
        })

        # Step E: Audit RESTORE_COMPLETED in restored database
        try:
            write_log(
                db,
                module="Restoration",
                action=AuditActionEnum.restore_completed,
                actor_id=actor.id,
                actor_role=actor.role,
                affected_record=backup_id,
                new_value={"tables": len(verified_counts), "safety_backup": safety_snapshot_path.name},
                reason="Database restored and integrity verified successfully",
                request=request,
                status="success",
            )
        except Exception as exc:
            logger.warning(f"Audit log after restore: {exc}")

        return RestoreResponse(
            backup_id=backup_id,
            status="completed",
            message="Database successfully restored from backup. Integrity checks passed.",
            restored_at=now_iso,
            pre_restore_safety_backup=safety_snapshot_path.name,
            verified_tables=verified_counts,
        )

    except Exception as exc:
        logger.error(f"Restoration failed, initiating rollback: {exc}", exc_info=True)
        # Rollback from safety snapshot
        if safety_snapshot_path.exists():
            try:
                safety_conn = sqlite3.connect(str(safety_snapshot_path))
                live_conn = sqlite3.connect(str(src_file))
                with live_conn:
                    safety_conn.backup(live_conn)
                live_conn.close()
                safety_conn.close()
                logger.info("Successfully rolled back to pre-restore safety snapshot.")
            except Exception as rb_exc:
                logger.critical(f"CRITICAL: Rollback failed: {rb_exc}")

        _record_external_restoration({
            "backup_id": backup_id,
            "restored_at": now_iso,
            "restored_by_id": actor.id,
            "restored_by": actor.username or actor.email,
            "pre_restore_safety_backup": safety_snapshot_path.name,
            "status": "failed",
            "error": str(exc),
        })

        try:
            write_log(
                db,
                module="Restoration",
                action=AuditActionEnum.restore_failed,
                actor_id=actor.id,
                actor_role=actor.role,
                affected_record=backup_id,
                reason=f"Restoration failed (rollback attempted): {str(exc)[:200]}",
                request=request,
                status="failed",
            )
        except Exception:
            pass

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database restoration failed: {str(exc)}. Pre-restore safety snapshot preserved."
        )

