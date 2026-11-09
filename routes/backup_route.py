"""
Admin Backup and Restore API Routes.

Provides protected endpoints for database backup creation, verification,
history listing, download, dry-run sandbox recovery, and safe restoration.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from models.accounts import Accounts
from schemas.backup_schema import (
    BackupCreateRequest,
    BackupItemOut,
    BackupVerifyResponse,
    DatabaseStatusResponse,
    DryRunRestoreResponse,
    RestorePreviewResponse,
    RestoreRequest,
    RestoreResponse,
)
from services.backup_service import (
    create_database_backup,
    get_download_file,
    get_system_status,
    list_backups,
    verify_backup_integrity,
)
from services.restore_service import (
    dry_run_sandbox_restore,
    execute_database_restore,
    preview_restore,
)
from utils.admin_guard import require_admin
from utils.dependencies import get_db

router = APIRouter(prefix="/admin/backup", tags=["Admin Backup and Restore"])


@router.get("/status", response_model=DatabaseStatusResponse)
def get_backup_status(
    db: Session = Depends(get_db),
    admin: Accounts = Depends(require_admin),
):
    """Retrieve active database status, engine type, and backup readiness."""
    return get_system_status(db)


@router.get("/list", response_model=List[BackupItemOut])
def get_backup_history(
    db: Session = Depends(get_db),
    admin: Accounts = Depends(require_admin),
):
    """Retrieve full history of backups from the protected manifest."""
    return list_backups()


@router.post("/create", response_model=BackupItemOut, status_code=status.HTTP_201_CREATED)
def create_backup(
    payload: Optional[BackupCreateRequest] = None,
    request: Request = None,
    db: Session = Depends(get_db),
    admin: Accounts = Depends(require_admin),
):
    """Initiate an atomic, consistent database backup and record audit logs."""
    return create_database_backup(db, actor=admin, request=request, payload=payload)


@router.post("/{backup_id}/verify", response_model=BackupVerifyResponse)
def verify_backup(
    backup_id: str,
    request: Request = None,
    db: Session = Depends(get_db),
    admin: Accounts = Depends(require_admin),
):
    """Perform cryptographic SHA-256 and database structure verification."""
    return verify_backup_integrity(backup_id, db=db, actor=admin, request=request)


@router.get("/{backup_id}/download")
def download_backup(
    backup_id: str,
    db: Session = Depends(get_db),
    admin: Accounts = Depends(require_admin),
):
    """Download an authorized backup artifact."""
    file_path, filename = get_download_file(backup_id)
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream",
    )


@router.post("/{backup_id}/preview", response_model=RestorePreviewResponse)
def get_restore_preview(
    backup_id: str,
    db: Session = Depends(get_db),
    admin: Accounts = Depends(require_admin),
):
    """Generate pre-restoration compatibility review, safety checks, and risk warnings."""
    return preview_restore(backup_id, db=db)


@router.post("/{backup_id}/test-restore", response_model=DryRunRestoreResponse)
def test_restore_staging(
    backup_id: str,
    request: Request = None,
    db: Session = Depends(get_db),
    admin: Accounts = Depends(require_admin),
):
    """Perform a safe dry-run restore into an isolated sandbox without altering live data."""
    return dry_run_sandbox_restore(backup_id, db=db, actor=admin, request=request)


@router.post("/{backup_id}/restore", response_model=RestoreResponse)
def restore_backup(
    backup_id: str,
    payload: RestoreRequest,
    request: Request = None,
    db: Session = Depends(get_db),
    admin: Accounts = Depends(require_admin),
):
    """Execute guarded database restoration with safety snapshots and integrity verification."""
    return execute_database_restore(
        backup_id=backup_id,
        confirmation_text=payload.confirmation_text,
        db=db,
        actor=admin,
        request=request,
    )

