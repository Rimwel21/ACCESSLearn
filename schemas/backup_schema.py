"""
Backup and Restore Pydantic Schemas.
"""
from typing import Optional, Dict, List
from pydantic import BaseModel, Field


class DatabaseStatusResponse(BaseModel):
    active_database: str
    engine_type: str
    database_name: str
    host: Optional[str] = None
    backup_capable: bool
    restore_capable: bool
    backup_storage_path: str
    total_backups: int
    last_backup_time: Optional[str] = None
    last_verified_time: Optional[str] = None
    environment: str
    production_safeguards_active: bool
    status_message: str


class BackupItemOut(BaseModel):
    backup_id: str
    filename: str
    created_at: str
    backup_type: str = "full"
    database_engine: str
    file_size: int
    file_size_human: str
    checksum_sha256: str
    status: str  # completed | failed | corrupted
    integrity_status: str  # verified | unverified | corrupted
    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None
    table_counts: Optional[Dict[str, int]] = None
    notes: Optional[str] = None


class BackupCreateRequest(BaseModel):
    backup_type: str = Field(default="full", max_length=50)
    notes: Optional[str] = Field(default=None, max_length=500)


class BackupVerifyResponse(BaseModel):
    backup_id: str
    integrity_status: str
    computed_checksum: str
    expected_checksum: str
    checksum_matches: bool
    structure_valid: bool
    details: str
    verified_at: str


class RestorePreviewResponse(BaseModel):
    backup_id: str
    database_engine: str
    created_at: str
    file_size_human: str
    checksum_sha256: str
    target_database: str
    target_environment: str
    can_restore: bool
    restriction_reason: Optional[str] = None
    table_counts: Optional[Dict[str, int]] = None
    warnings: List[str]
    safety_measures: List[str]
    required_confirmation_text: str = "RESTORE"


class RestoreRequest(BaseModel):
    confirmation_text: str = Field(..., max_length=50)


class RestoreResponse(BaseModel):
    backup_id: str
    status: str
    message: str
    restored_at: str
    pre_restore_safety_backup: Optional[str] = None
    verified_tables: Optional[Dict[str, int]] = None


class DryRunRestoreResponse(BaseModel):
    backup_id: str
    status: str
    message: str
    sandbox_verified: bool
    table_counts: Dict[str, int]
    duration_ms: float

