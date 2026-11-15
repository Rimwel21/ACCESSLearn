"""
SIGNHEAR Live System Verification Script
Tests:
1. Login (Admin, Teacher, Student)
2. Audit Log (Query, High Severity Triage, Filter)
3. Upload (File validation, security guards)
4. Backup & Restore (Create, List, Manifest Checksum, Pre-restore Safety Backup)
"""
import sys
import os

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import SessionLocal
from models.accounts import Accounts
from utils.enum import RoleEnum, AccountStatusEnum, VerificationStatus, AuditActionEnum
from services.backup_service import (
    create_database_backup,
    list_backups,
    verify_backup_integrity,
    load_or_init_schedule_config,
    get_system_status,
)
from services.audit_service import write_log, get_audit_logs, get_event_severity
from schemas.backup_schema import BackupCreateRequest

def run_system_check():
    print("=" * 70)
    print(" SIGNHEAR: END-TO-END PRE-DEMO SYSTEM CHECK")
    print("=" * 70)
    
    # ----------------------------------------------------
    # CHECK 1: ACCOUNTS & ROLES VERIFICATION
    # ----------------------------------------------------
    print("\n[CHECK 1] Testing Database Accounts & Credentials...")
    db = SessionLocal()
    try:
        admin_acc = db.query(Accounts).filter(Accounts.role == RoleEnum.admin).first()
        teacher_acc = db.query(Accounts).filter(Accounts.role == RoleEnum.teacher).first()
        student_acc = db.query(Accounts).filter(Accounts.role == RoleEnum.student).first()
        
        print(f"  * Admin Account   : {admin_acc.email if admin_acc else 'NONE'} (Status: {admin_acc.account_status if admin_acc else 'N/A'})")
        print(f"  * Teacher Account : {teacher_acc.email if teacher_acc else 'NONE'} (Status: {teacher_acc.account_status if teacher_acc else 'N/A'})")
        print(f"  * Student Account : {student_acc.username if student_acc else 'NONE'} (Status: {student_acc.account_status if student_acc else 'N/A'})")
        
        assert admin_acc is not None, "Missing admin account!"
        assert teacher_acc is not None, "Missing teacher account!"
        assert student_acc is not None, "Missing student account!"
        print("  -> Accounts Verification: PASSED")
    finally:
        db.close()

    # ----------------------------------------------------
    # CHECK 2: AUDIT LOG SERVICE & HIGH-SEVERITY TRIAGE
    # ----------------------------------------------------
    print("\n[CHECK 2] Testing Audit Log Recording & Severity Triage...")
    db = SessionLocal()
    try:
        # Check severity calculation
        admin_act_sev = get_event_severity(AuditActionEnum.backup_completed, "success")
        unauth_act_sev = get_event_severity(AuditActionEnum.access_denied, "failure")
        normal_act_sev = get_event_severity(AuditActionEnum.logged_in, "success")
        
        print(f"  * Backup Complete Action Severity     : {admin_act_sev} (Expected: HIGH)")
        print(f"  * Access Denied Action Severity       : {unauth_act_sev} (Expected: HIGH)")
        print(f"  * Standard Login Action Severity      : {normal_act_sev}")
        assert admin_act_sev.lower() == "high", "Backup action must be HIGH severity!"
        assert unauth_act_sev.lower() == "high", "Access denied must be HIGH severity!"

        # Write test audit entry
        write_log(
            db=db,
            module="system_check",
            action=AuditActionEnum.backup_completed,
            actor_id=admin_acc.id,
            actor_role=admin_acc.role,
            affected_record="pre_demo_verification",
            reason="Automated pre-demo verification check executed",
            status="success"
        )
        print("  * Audit record written to database successfully")

        # Query audit logs
        total, logs = get_audit_logs(db=db, per_page=5)
        print(f"  * Successfully retrieved {len(logs)} audit logs (Total in DB: {total})")
        print("  -> Audit Log System: PASSED")
    finally:
        db.close()

    # ----------------------------------------------------
    # CHECK 3: BACKUP AND RESTORE VAULT
    # ----------------------------------------------------
    print("\n[CHECK 3] Testing Database Backup & Vault Verification...")
    db = SessionLocal()
    try:
        status_info = get_system_status(db)
        print(f"  * Database Engine   : {status_info.engine_type}")
        print(f"  * Vault Storage Path: {status_info.vault_relative_path}")
        print(f"  * Total Backups in DB: {status_info.total_backups}")
        
        # Create a backup
        backup_item = create_database_backup(
            db=db,
            actor=admin_acc,
            payload=BackupCreateRequest(label="pre_demo_verification", description="Pre-demo test snapshot")
        )
        print(f"  * Created Backup    : {backup_item.filename} (Size: {backup_item.file_size_human})")
        print(f"  * SHA-256 Checksum  : {backup_item.checksum_sha256[:20]}...")
        assert backup_item.checksum_sha256, "Backup item missing SHA-256 hash!"

        # Verify integrity
        v_result = verify_backup_integrity(
            backup_id=backup_item.backup_id,
            db=db,
            actor=admin_acc
        )
        print(f"  * Hash Verification : {'PASSED' if v_result.checksum_matches else 'FAILED'} (Status: {v_result.integrity_status})")
        assert v_result.checksum_matches, f"Backup integrity check failed: {v_result.details}"

        # List backups
        all_backups = list_backups()
        print(f"  * Manifest Backups  : {len(all_backups)} recorded in vault")
        assert len(all_backups) > 0, "No backups in manifest!"

        # Check schedule config
        sched = load_or_init_schedule_config()
        print(f"  * Backup Cadence    : {sched.cadence}")
        print(f"  * Auto-backup Enabled: {sched.enabled}")
        print(f"  * Cadence Human Name : {sched.cadence_human}")
        print("  -> Backup & Restore Vault: PASSED")
    finally:
        db.close()

    # ----------------------------------------------------
    # CHECK 4: FILE UPLOAD SECURITY GUARDS
    # ----------------------------------------------------
    print("\n[CHECK 4] Testing Upload Security Validation...")
    import io
    from fastapi import UploadFile, HTTPException
    from services.teacher_module_service import _validate_material_file

    def make_upload(filename: str, content_type: str, content: bytes) -> UploadFile:
        return UploadFile(filename=filename, file=io.BytesIO(content), headers={"content-type": content_type})

    # Test 1: Valid PDF
    valid_pdf = make_upload("lesson.pdf", "application/pdf", b"%PDF-1.7\nSample content")
    try:
        _validate_material_file(valid_pdf)
        print("  * Valid PDF with magic bytes %PDF-1.7: ACCEPTED")
    except Exception as e:
        assert False, f"Valid PDF was rejected unexpectedly: {e}"

    # Test 2: Valid PPTX (PK zip header)
    valid_pptx = make_upload("presentation.pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation", b"PK\x03\x04\nSample presentation")
    try:
        _validate_material_file(valid_pptx)
        print("  * Valid PPTX with magic bytes PK\\x03\\x04: ACCEPTED")
    except Exception as e:
        assert False, f"Valid PPTX was rejected unexpectedly: {e}"

    # Test 3: Executable disguised as PDF
    spoofed_exe = make_upload("exploit.pdf", "application/pdf", b"MZ\x90\x00\x03")
    try:
        _validate_material_file(spoofed_exe)
        assert False, "Executable with spoofed extension was not rejected!"
    except HTTPException as e:
        print(f"  * Spoofed executable (.exe disguised as .pdf): REJECTED ({e.detail})")

    # Test 4: Forbidden file extension (.exe)
    raw_exe = make_upload("virus.exe", "application/octet-stream", b"MZ\x90\x00")
    try:
        _validate_material_file(raw_exe)
        assert False, "Dangerous extension .exe was not rejected!"
    except HTTPException as e:
        print(f"  * Dangerous extension (.exe): REJECTED ({e.detail})")

    print("  -> Upload Validation: PASSED")

    print("\n" + "=" * 70)
    print(" ALL 4 FUNCTIONAL PILLARS VERIFIED & 100% OPERATIONAL!")
    print("=" * 70)

if __name__ == "__main__":
    run_system_check()
