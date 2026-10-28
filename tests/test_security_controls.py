import unittest
from datetime import datetime, timedelta, timezone
from io import BytesIO

from fastapi import HTTPException, Request, Response, UploadFile
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.datastructures import Headers

import models  # noqa: F401 - register all mapped tables
from auth.account_auth import create_access_token, hash_password
from core.config import settings
from database.connection import Base
from main import app
from models.accounts import Accounts
from models.audit_log import AuditLog
from schemas.accounts_schema import AccountLogin
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
