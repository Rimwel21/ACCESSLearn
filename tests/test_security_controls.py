import json
import unittest
from datetime import datetime, timedelta, timezone
from io import BytesIO
from unittest.mock import patch

from fastapi import HTTPException, Request, Response, UploadFile
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from jose import jwt
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.datastructures import Headers

import models  # noqa: F401 - register all mapped tables
from auth.account_auth import create_access_token, create_refresh_token, hash_password
from core.config import settings
from database.connection import Base
from main import app
from models.accounts import Accounts
from models.audit_log import AuditLog
from routes.refresh_token import refresh_token as refresh_access_token
from schemas.accounts_schema import AccountLogin
from services.audit_service import write_log
from services.auth_service import user_login
from services.teacher_module_service import _validate_material_file
from utils.admin_guard import require_admin
from utils.dependencies import get_current_user
from utils.enum import AccountStatusEnum, AuditActionEnum, RoleEnum, VerificationStatus
from utils.password_policy import validate_new_password
from utils.teacher_guard import require_teacher


def request_for(path: str = "/security-test") -> Request:
    return Request({
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "https",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [(b"user-agent", b"security-test")],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 443),
    })


def request_with_refresh_cookie(token: str) -> Request:
    return Request({
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "scheme": "https",
        "path": "/api/refresh",
        "raw_path": b"/api/refresh",
        "query_string": b"",
        "headers": [
            (b"cookie", f"refresh_token={token}".encode()),
            (b"user-agent", b"security-test"),
        ],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 443),
    })


def upload(filename: str, content_type: str, content: bytes) -> UploadFile:
    return UploadFile(
        file=BytesIO(content),
        filename=filename,
        headers=Headers({"content-type": content_type}),
    )


class SecurityControlTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.db = self.Session()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def account(self, role: RoleEnum, *, username=None, email=None, password="StrongPass123"):
        account = Accounts(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            role=role,
            verification_status=VerificationStatus.verified,
            account_status=AccountStatusEnum.active,
        )
        self.db.add(account)
        self.db.commit()
        return account

    def credentials_for(self, account: Accounts):
        return HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=create_access_token({"sub": str(account.id), "role": account.role.value}),
        )

    def test_new_password_policy_rejects_weak_values(self):
        self.assertEqual(validate_new_password("Learning123"), "Learning123")
        for weak in ("password", "onlyletters", "12345678", " Space123", "Space 123"):
            with self.subTest(password=weak), self.assertRaises(ValueError):
                validate_new_password(weak)

    def test_login_identifier_is_normalized_and_requires_one_choice(self):
        login = AccountLogin(
            username="  learner1  ",
            password="StrongPass123",
            role=RoleEnum.student,
        )
        self.assertEqual(login.username, "learner1")

        invalid_payloads = [
            {"password": "StrongPass123", "role": RoleEnum.student},
            {
                "username": "learner1",
                "email": "learner@example.com",
                "password": "StrongPass123",
                "role": RoleEnum.student,
            },
            {"username": "learn\x00er", "password": "StrongPass123", "role": RoleEnum.student},
        ]
        for payload in invalid_payloads:
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                AccountLogin(**payload)

    def test_access_and_refresh_tokens_cannot_be_substituted(self):
        student = self.account(RoleEnum.student, username="tokenstudent")
        access_token = create_access_token({"sub": str(student.id), "role": student.role.value})
        refresh_token = create_refresh_token({"sub": str(student.id)})

        access_claims = jwt.decode(access_token, settings.secret_key, algorithms=[settings.algorithm])
        refresh_claims = jwt.decode(refresh_token, settings.secret_key, algorithms=[settings.algorithm])
        self.assertEqual(access_claims["token_type"], "access")
        self.assertEqual(refresh_claims["token_type"], "refresh")

        with self.assertRaises(HTTPException) as bearer_rejected:
            get_current_user(
                request_for(),
                HTTPAuthorizationCredentials(scheme="Bearer", credentials=refresh_token),
                self.db,
            )
        self.assertEqual(bearer_rejected.exception.status_code, 401)

        with self.assertRaises(HTTPException) as cookie_rejected:
            refresh_access_token(request_with_refresh_cookie(access_token), self.db)
        self.assertEqual(cookie_rejected.exception.status_code, 401)

        refreshed = refresh_access_token(request_with_refresh_cookie(refresh_token), self.db)
        refreshed_claims = jwt.decode(
            refreshed["access_token"],
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        self.assertEqual(refreshed_claims["token_type"], "access")

    def test_audit_log_redacts_secrets_and_bounds_request_metadata(self):
        long_user_agent = "client/1.0 " + "x" * 700
        request = Request({
            "type": "http",
            "http_version": "1.1",
            "method": "POST",
            "scheme": "https",
            "path": "/security-test",
            "raw_path": b"/security-test",
            "query_string": b"",
            "headers": [(b"user-agent", long_user_agent.encode())],
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 443),
        })
        write_log(
            self.db,
            module="Authentication",
            action=AuditActionEnum.login_failed,
            affected_record="token=raw-token-value",
            old_value={
                "password": "PlaintextPass123",
                "nested": {"access_token": "signed-token", "safe": "kept"},
            },
            reason="Authorization failed: Bearer signed-token",
            request=request,
            status="failed",
        )

        entry = self.db.query(AuditLog).one()
        stored = json.loads(entry.old_value)
        self.assertEqual(stored["password"], "[REDACTED]")
        self.assertEqual(stored["nested"]["access_token"], "[REDACTED]")
        self.assertEqual(stored["nested"]["safe"], "kept")
        self.assertNotIn("raw-token-value", entry.affected_record)
        self.assertNotIn("signed-token", entry.reason)
        self.assertLessEqual(len(entry.user_agent), 512)

    def test_login_success_and_failed_attempts_are_audited(self):
        student = self.account(RoleEnum.student, username="learner1")
        response = Response()
        result = user_login(
            request_for("/auth/account/login"),
            AccountLogin(username="learner1", password="StrongPass123", role=RoleEnum.student),
            response,
            self.db,
        )
        self.assertIn("access_token", result)
        self.assertIn("refresh_token=", response.headers["set-cookie"])

        with self.assertRaises(HTTPException) as incorrect:
            user_login(
                request_for("/auth/account/login"),
                AccountLogin(username="learner1", password="WrongPass123", role=RoleEnum.student),
                Response(),
                self.db,
            )
        self.assertEqual(incorrect.exception.status_code, 401)

        with self.assertRaises(HTTPException) as missing:
            user_login(
                request_for("/auth/account/login"),
                AccountLogin(username="missing1", password="WrongPass123", role=RoleEnum.student),
                Response(),
                self.db,
            )
        self.assertEqual(missing.exception.status_code, 401)
        actions = [row.action for row in self.db.query(AuditLog).all()]
        self.assertIn(AuditActionEnum.logged_in, actions)
        self.assertGreaterEqual(actions.count(AuditActionEnum.login_failed), 2)
        self.assertEqual(student.account_status, AccountStatusEnum.active)

    def test_blocked_account_cannot_reuse_existing_access_token(self):
        student = self.account(RoleEnum.student, username="blocked1")
        credentials = self.credentials_for(student)
        student.verification_status = VerificationStatus.blocked
        student.account_status = AccountStatusEnum.suspended
        self.db.commit()

        with self.assertRaises(HTTPException) as denied:
            get_current_user(request_for("/student/modules"), credentials, self.db)
        self.assertEqual(denied.exception.status_code, 403)

    def test_invalid_and_expired_tokens_are_rejected(self):
        with self.assertRaises(HTTPException) as invalid:
            get_current_user(
                request_for(),
                HTTPAuthorizationCredentials(scheme="Bearer", credentials="not-a-jwt"),
                self.db,
            )
        self.assertEqual(invalid.exception.status_code, 401)

        expired_token = jwt.encode(
            {"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
            settings.secret_key,
            algorithm=settings.algorithm,
        )
        with self.assertRaises(HTTPException) as expired:
            get_current_user(
                request_for(),
                HTTPAuthorizationCredentials(scheme="Bearer", credentials=expired_token),
                self.db,
            )
        self.assertEqual(expired.exception.status_code, 401)

    def test_role_guards_reject_cross_role_access(self):
        student = self.account(RoleEnum.student, username="student2")
        teacher = self.account(RoleEnum.teacher, email="teacher2@example.com")

        with self.assertRaises(HTTPException) as teacher_denied:
            require_teacher(request_for("/teacher/modules"), student, self.db)
        self.assertEqual(teacher_denied.exception.status_code, 403)

        with self.assertRaises(HTTPException) as admin_denied_student:
            require_admin(request_for("/admin/accounts"), student, self.db)
        self.assertEqual(admin_denied_student.exception.status_code, 403)

        with self.assertRaises(HTTPException) as admin_denied_teacher:
            require_admin(request_for("/admin/accounts"), teacher, self.db)
        self.assertEqual(admin_denied_teacher.exception.status_code, 403)

    def test_unauthenticated_route_and_security_headers(self):
        client = TestClient(app)
        response = client.get("/auth/me")
        self.assertIn(response.status_code, {401, 403})
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertEqual(response.headers["x-frame-options"], "DENY")
        self.assertEqual(response.headers["referrer-policy"], "no-referrer")
        self.assertEqual(response.headers["cache-control"], "no-store")

        logout_response = client.post("/api/logout")
        self.assertEqual(logout_response.status_code, 204)
        self.assertIn("refresh_token=", logout_response.headers["set-cookie"])

    def test_production_cookie_setting_is_secure(self):
        original_environment = settings.environment
        original_secure = settings.refresh_cookie_secure
        try:
            settings.environment = "production"
            settings.refresh_cookie_secure = False
            self.assertTrue(settings.use_secure_cookies)
        finally:
            settings.environment = original_environment
            settings.refresh_cookie_secure = original_secure

    def test_material_upload_accepts_valid_signature(self):
        material = upload("lesson.pdf", "application/pdf", b"%PDF-1.7\ncontent")
        _validate_material_file(material, "PDF")

    def test_material_upload_accepts_large_presentation_within_configured_limit(self):
        original_limit = settings.max_material_upload_mb
        try:
            settings.max_material_upload_mb = 100
            material = upload(
                "lesson.pptx",
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                b"PK\x03\x04presentation",
            )
            with patch("services.teacher_module_service._upload_file_size", return_value=80 * 1024 * 1024):
                _validate_material_file(material, "PPTX")
        finally:
            settings.max_material_upload_mb = original_limit

    def test_material_upload_rejects_bad_extension_mime_signature_and_size(self):
        cases = [
            upload("lesson.exe", "application/octet-stream", b"MZ"),
            upload("lesson.pdf", "text/plain", b"%PDF-1.7"),
            upload("lesson.pdf", "application/pdf", b"not a pdf"),
        ]
        for material in cases:
            with self.subTest(filename=material.filename), self.assertRaises(HTTPException):
                _validate_material_file(material, "PDF")

        original_limit = settings.max_material_upload_mb
        try:
            settings.max_material_upload_mb = 1
            oversized = upload("large.pdf", "application/pdf", b"%PDF-" + b"0" * (1024 * 1024))
            with self.assertRaises(HTTPException) as rejected:
                _validate_material_file(oversized, "PDF")
            self.assertEqual(rejected.exception.status_code, 413)
        finally:
            settings.max_material_upload_mb = original_limit


if __name__ == "__main__":
    unittest.main()
