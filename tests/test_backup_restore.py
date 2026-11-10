import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import models  # noqa: F401
from auth.account_auth import create_access_token, hash_password
from core.config import settings
from database.connection import Base
from main import app
from models.accounts import Accounts
from models.audit_log import AuditLog
from services.backup_service import BACKUP_DIR, MANIFEST_PATH
from utils.dependencies import get_db
from utils.enum import AccountStatusEnum, AuditActionEnum, RoleEnum, VerificationStatus


class BackupRestoreSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Setup temporary test directory for databases and backups
        cls.test_dir = tempfile.mkdtemp(prefix="signhear_backup_test_")
        cls.test_db_path = Path(cls.test_dir) / "test_local.db"
        cls.test_backup_dir = Path(cls.test_dir) / "backups"
        cls.test_backup_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_dir, ignore_errors=True)

    def setUp(self):
        # Create fresh SQLite test database
        if self.test_db_path.exists():
            self.test_db_path.unlink()

        self.engine = create_engine(
            f"sqlite:///{self.test_db_path}",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.db = self.Session()

        def override_get_db():
            db = self.Session()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

        # Create test users
        self.admin = Accounts(
            username="test_admin",
            email="admin@signhear.org",
            hashed_password=hash_password("AdminPass123!"),
            role=RoleEnum.admin,
            verification_status=VerificationStatus.verified,
            account_status=AccountStatusEnum.active,
        )
        self.teacher = Accounts(
            username="test_teacher",
            email="teacher@signhear.org",
            hashed_password=hash_password("TeacherPass123!"),
            role=RoleEnum.teacher,
            verification_status=VerificationStatus.verified,
            account_status=AccountStatusEnum.active,
        )
        self.student = Accounts(
            username="test_student",
            email="student@signhear.org",
            hashed_password=hash_password("StudentPass123!"),
            role=RoleEnum.student,
            verification_status=VerificationStatus.verified,
            account_status=AccountStatusEnum.active,
        )
        self.blocked_admin = Accounts(
            username="blocked_admin",
            email="blocked@signhear.org",
            hashed_password=hash_password("AdminPass123!"),
            role=RoleEnum.admin,
            verification_status=VerificationStatus.blocked,
            account_status=AccountStatusEnum.suspended,
        )

        self.db.add_all([self.admin, self.teacher, self.student, self.blocked_admin])
        self.db.commit()

        self.admin_token = create_access_token({"sub": str(self.admin.id), "role": self.admin.role.value})
        self.teacher_token = create_access_token({"sub": str(self.teacher.id), "role": self.teacher.role.value})
        self.student_token = create_access_token({"sub": str(self.student.id), "role": self.student.role.value})
        self.blocked_admin_token = create_access_token({"sub": str(self.blocked_admin.id), "role": self.blocked_admin.role.value})

    def tearDown(self):
        self.db.close()
        self.engine.dispose()
        app.dependency_overrides.clear()

    def test_unauthenticated_cannot_access_backup_endpoints(self):
        res1 = self.client.get("/admin/backup/status")
        self.assertIn(res1.status_code, (401, 403))

        res2 = self.client.post("/admin/backup/create", json={"notes": "test"})
        self.assertIn(res2.status_code, (401, 403))

        res3 = self.client.get("/admin/backup/list")
        self.assertIn(res3.status_code, (401, 403))

    def test_non_admin_roles_are_forbidden(self):
        # Student
        res_stud = self.client.get(
            "/admin/backup/status",
            headers={"Authorization": f"Bearer {self.student_token}"}
        )
        self.assertEqual(res_stud.status_code, 403)

        # Teacher
        res_teach = self.client.post(
            "/admin/backup/create",
            headers={"Authorization": f"Bearer {self.teacher_token}"},
            json={"notes": "hack attempt"}
        )
        self.assertEqual(res_teach.status_code, 403)

        # Blocked Admin
        res_blocked = self.client.get(
            "/admin/backup/status",
            headers={"Authorization": f"Bearer {self.blocked_admin_token}"}
        )
        self.assertEqual(res_blocked.status_code, 403)

    def test_admin_can_query_status(self):
        with patch("services.backup_service.detect_database_info") as mock_detect:
            mock_detect.return_value = {
                "engine": "sqlite",
                "active_database": "SQLite",
                "database_name": "test_local.db",
                "host": "localhost (local file)",
                "file_path": self.test_db_path,
                "backup_capable": True,
                "restore_capable": True,
                "production_safeguards": False,
                "message": "Local SQLite active.",
            }
            res = self.client.get(
                "/admin/backup/status",
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["engine_type"], "sqlite")
            self.assertTrue(data["backup_capable"])
            self.assertTrue(data["restore_capable"])

    def test_create_and_verify_sqlite_backup_lifecycle(self):
        with patch("services.backup_service.detect_database_info") as mock_detect, \
             patch("services.backup_service.BACKUP_DIR", self.test_backup_dir), \
             patch("services.backup_service.MANIFEST_PATH", self.test_backup_dir / "manifest.json"), \
             patch("services.restore_service.BACKUP_DIR", self.test_backup_dir), \
             patch("services.restore_service.detect_database_info") as mock_restore_detect:

            db_info = {
                "engine": "sqlite",
                "active_database": "SQLite",
                "database_name": "test_local.db",
                "host": "localhost",
                "file_path": self.test_db_path,
                "backup_capable": True,
                "restore_capable": True,
                "production_safeguards": False,
                "message": "Local SQLite active.",
            }
            mock_detect.return_value = db_info
            mock_restore_detect.return_value = db_info

            # 1. Create Backup
            create_res = self.client.post(
                "/admin/backup/create",
                headers={"Authorization": f"Bearer {self.admin_token}"},
                json={"notes": "Automated test backup"}
            )
            self.assertEqual(create_res.status_code, 201)
            bdata = create_res.json()
            backup_id = bdata["backup_id"]
            self.assertTrue(backup_id.startswith("backup_"))
            self.assertEqual(bdata["integrity_status"], "verified")
            self.assertIn("accounts", bdata["table_counts"])
            self.assertGreater(bdata["file_size"], 0)

            # Check audit logs for backup
            audit_events = self.db.query(AuditLog).filter(AuditLog.module == "Backup").all()
            actions = [a.action for a in audit_events]
            self.assertIn(AuditActionEnum.backup_requested, actions)
            self.assertIn(AuditActionEnum.backup_started, actions)
            self.assertIn(AuditActionEnum.backup_completed, actions)

            # 2. Verify Backup
            verify_res = self.client.post(
                f"/admin/backup/{backup_id}/verify",
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )
            self.assertEqual(verify_res.status_code, 200)
            vdata = verify_res.json()
            self.assertEqual(vdata["integrity_status"], "verified")
            self.assertTrue(vdata["checksum_matches"])
            self.assertTrue(vdata["structure_valid"])

            # 3. List Backups
            list_res = self.client.get(
                "/admin/backup/list",
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )
            self.assertEqual(list_res.status_code, 200)
            items = list_res.json()
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]["backup_id"], backup_id)

            # 4. Dry-run Sandbox Restore
            dry_run_res = self.client.post(
                f"/admin/backup/{backup_id}/test-restore",
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )
            self.assertEqual(dry_run_res.status_code, 200)
            dr_data = dry_run_res.json()
            self.assertEqual(dr_data["status"], "passed")
            self.assertTrue(dr_data["sandbox_verified"])
            self.assertIn("accounts", dr_data["table_counts"])

            # 5. Restore Preview
            preview_res = self.client.post(
                f"/admin/backup/{backup_id}/preview",
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )
            self.assertEqual(preview_res.status_code, 200)
            pdata = preview_res.json()
            self.assertTrue(pdata["can_restore"])
            self.assertEqual(pdata["required_confirmation_text"], "RESTORE")

            # 6. Safe Restore Execution
            # Modify active DB first
            new_student = Accounts(
                username="student_after_backup",
                email="after@signhear.org",
                hashed_password="pw",
                role=RoleEnum.student,
                verification_status=VerificationStatus.verified,
                account_status=AccountStatusEnum.active,
            )
            self.db.add(new_student)
            self.db.commit()
            self.assertEqual(self.db.query(Accounts).filter_by(username="student_after_backup").count(), 1)

            restore_res = self.client.post(
                f"/admin/backup/{backup_id}/restore",
                headers={"Authorization": f"Bearer {self.admin_token}"},
                json={"confirmation_text": "RESTORE"}
            )
            self.assertEqual(restore_res.status_code, 200)
            rdata = restore_res.json()
            self.assertEqual(rdata["status"], "completed")
            self.assertIsNotNone(rdata["pre_restore_safety_backup"])

            # Verify active DB restored (student_after_backup should no longer be in restored snapshot)
            fresh_db = self.Session()
            self.assertEqual(fresh_db.query(Accounts).filter_by(username="student_after_backup").count(), 0)
            fresh_db.close()

    def test_tampered_backup_fails_verification(self):
        with patch("services.backup_service.detect_database_info") as mock_detect, \
             patch("services.backup_service.BACKUP_DIR", self.test_backup_dir), \
             patch("services.backup_service.MANIFEST_PATH", self.test_backup_dir / "manifest.json"):

            mock_detect.return_value = {
                "engine": "sqlite",
                "active_database": "SQLite",
                "database_name": "test_local.db",
                "host": "localhost",
                "file_path": self.test_db_path,
                "backup_capable": True,
                "restore_capable": True,
                "production_safeguards": False,
                "message": "Local SQLite active.",
            }

            create_res = self.client.post(
                "/admin/backup/create",
                headers={"Authorization": f"Bearer {self.admin_token}"},
            )
            backup_id = create_res.json()["backup_id"]
            backup_file = self.test_backup_dir / f"{backup_id}.db"

            # Corrupt the backup file
            with open(backup_file, "ab") as f:
                f.write(b"TAMPERED_BYTES")

            verify_res = self.client.post(
                f"/admin/backup/{backup_id}/verify",
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )
            self.assertEqual(verify_res.status_code, 200)
            vdata = verify_res.json()
            self.assertEqual(vdata["integrity_status"], "corrupted")
            self.assertFalse(vdata["checksum_matches"])

    def test_path_traversal_is_blocked(self):
        malicious_ids = ["../etc/passwd", "..\\secret", "backup/sub", "backup*id"]
        for bad_id in malicious_ids:
            with self.subTest(bad_id=bad_id):
                res = self.client.get(
                    f"/admin/backup/{bad_id}/download",
                    headers={"Authorization": f"Bearer {self.admin_token}"}
                )
                self.assertIn(res.status_code, (400, 404, 405))

    def test_production_postgresql_restore_is_restricted(self):
        with patch("services.restore_service.detect_database_info") as mock_detect:
            mock_detect.return_value = {
                "engine": "postgresql",
                "active_database": "PostgreSQL",
                "database_name": "postgres",
                "host": "supabase.aws.com",
                "file_path": None,
                "backup_capable": True,
                "restore_capable": False,
                "production_safeguards": True,
                "message": "Remote PostgreSQL active.",
            }

            res = self.client.post(
                "/admin/backup/backup_test_123/restore",
                headers={"Authorization": f"Bearer {self.admin_token}"},
                json={"confirmation_text": "RESTORE"}
            )
            self.assertEqual(res.status_code, 403)
            self.assertIn("restricted", res.json()["detail"].lower())

    def test_backup_schedule_cadence_and_persistence(self):
        # 1. Admin queries schedule defaults
        res = self.client.get(
            "/admin/backup/schedule",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["enabled"])
        self.assertEqual(data["vault_path"], "./backups/")
        self.assertIn("backups", data["manifest_path"])

        # 2. Update cadence to Every 1 Month
        update_res = self.client.post(
            "/admin/backup/schedule",
            headers={"Authorization": f"Bearer {self.admin_token}"},
            json={"cadence": "every_1_month", "enabled": True}
        )
        self.assertEqual(update_res.status_code, 200)
        updated_data = update_res.json()
        self.assertEqual(updated_data["cadence"], "every_1_month")
        self.assertEqual(updated_data["cadence_human"], "Every 1 Month")

    def test_system_severity_is_high_for_backup_and_access_denied(self):
        from services.audit_service import get_event_severity
        from utils.enum import AuditActionEnum

        # Backup lifecycle actions are HIGH in the system
        self.assertEqual(get_event_severity(AuditActionEnum.backup_requested), "high")
        self.assertEqual(get_event_severity(AuditActionEnum.backup_started), "high")
        self.assertEqual(get_event_severity(AuditActionEnum.backup_completed), "high")
        self.assertEqual(get_event_severity(AuditActionEnum.backup_verification_passed), "high")

        # Security threats / Access Denied are HIGH in the system
        self.assertEqual(get_event_severity(AuditActionEnum.access_denied), "high")
        self.assertEqual(get_event_severity(AuditActionEnum.login_failed), "high")

        # Failures are CRITICAL
        self.assertEqual(get_event_severity(AuditActionEnum.backup_failed, status="failed"), "critical")
        self.assertEqual(get_event_severity(AuditActionEnum.access_denied, status="failed"), "critical")


if __name__ == "__main__":
    unittest.main()
