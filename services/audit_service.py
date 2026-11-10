"""
Audit Log Service.

Provides write_log() for any service to call, plus paginated query
with rich filtering and export support.
"""
from __future__ import annotations
import json
import re
from datetime import datetime
from typing import Optional
from fastapi import Request
from sqlalchemy.orm import Session

from models.audit_log import AuditLog
from repositories.audit_log_repository import AuditLogRepository
from utils.enum import AuditActionEnum, RoleEnum


# Cybersecurity Plan §5 / Appendix A.5: audit evidence must not retain common
# password, token, cookie, OTP, or provider-secret fields.
_SENSITIVE_KEY_PARTS = (
    "password",
    "token",
    "secret",
    "authorization",
    "cookie",
    "otp",
    "api_key",
    "apikey",
)
_SECRET_TEXT_PATTERN = re.compile(
    r"(?i)\b(password|token|secret|otp|api[_-]?key)\s*[:=]\s*([^\s,;]+)"
)
_BEARER_PATTERN = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+")


def _is_sensitive_key(key: object) -> bool:
    normalized = str(key).strip().lower().replace("-", "_")
    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)


def _redact_structured_value(value):
    if isinstance(value, dict):
        return {
            str(key): "[REDACTED]" if _is_sensitive_key(key) else _redact_structured_value(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_redact_structured_value(item) for item in value]
    return value


def _safe_log_text(value: Optional[str], max_length: int) -> Optional[str]:
    if value is None:
        return None
    sanitized = _BEARER_PATTERN.sub("Bearer [REDACTED]", str(value))
    sanitized = _SECRET_TEXT_PATTERN.sub(lambda match: f"{match.group(1)}=[REDACTED]", sanitized)
    return sanitized[:max_length]


def _parse_ua(user_agent: str) -> tuple[str, str, str]:
    """Very basic UA parsing. Returns (browser, os_name, device_type)."""
    ua = user_agent.lower()
    browser = "Unknown"
    os_name = "Unknown"
    device  = "Desktop"

    if "chrome" in ua and "edg" not in ua:
        browser = "Chrome"
    elif "firefox" in ua:
        browser = "Firefox"
    elif "safari" in ua and "chrome" not in ua:
        browser = "Safari"
    elif "edg" in ua:
        browser = "Edge"
    elif "opera" in ua or "opr" in ua:
        browser = "Opera"

    if "windows" in ua:
        os_name = "Windows"
    elif "mac os" in ua:
        os_name = "macOS"
    elif "linux" in ua:
        os_name = "Linux"
    elif "android" in ua:
        os_name = "Android"
        device  = "Mobile"
    elif "iphone" in ua or "ipad" in ua:
        os_name = "iOS"
        device  = "Mobile" if "iphone" in ua else "Tablet"

    return browser, os_name, device


def get_event_severity(action: AuditActionEnum | str, status: str = "success") -> str:
    """Calculate normalized severity: critical, high, medium, or low."""
    act = action.value if isinstance(action, AuditActionEnum) else str(action).lower()
    stat = str(status).lower()
    
    # Critical: Direct destructive actions, failed integrity validation, or active restore execution
    if act in {"restore_failed", "restore_started", "restore_approved", "hard_deleted"}:
        return "critical"
    if stat == "failed" and act in {"access_denied", "restore_validation_failed", "backup_failed", "backup_verification_failed"}:
        return "critical"
        
    # High in the system: Backup & restore operations, access denials, authentication failures, and security controls
    # (Note: On paper in the Initial Risk Register, R1/R4/R8/R12 are prioritized as Medium per grade 4 scope rubric,
    # but in the live system implementation they are elevated to High severity for administrator visibility and alert triage)
    if (
        act in {
            "access_denied", "login_failed", "backup_failed", "restore_validation_failed",
            "backup_requested", "backup_started", "backup_completed", "backup_verification_started",
            "backup_verification_passed", "backup_verification_failed", "backup_schedule_updated",
            "restore_requested", "password_reset_requested", "password_reset_completed",
            "bulk_action", "deactivated"
        }
        or "backup" in act
        or "restore" in act
    ):
        return "high"
    if stat == "failed":
        return "high"
        
    if act in {
        "created", "updated", "assigned", "archived",
        "restored", "transferred", "activated"
    }:
        return "medium"
        
    return "low"


def write_log(
    db:              Session,
    *,
    module:          str,
    action:          AuditActionEnum | str,
    actor_id:        Optional[int]   = None,
    actor_role:      Optional[RoleEnum] = None,
    affected_record: Optional[str]   = None,
    old_value:       Optional[dict]  = None,
    new_value:       Optional[dict]  = None,
    old_section_id:  Optional[int]   = None,
    new_section_id:  Optional[int]   = None,
    old_teacher_id:  Optional[int]   = None,
    new_teacher_id:  Optional[int]   = None,
    reason:          Optional[str]   = None,
    request:         Optional[Request] = None,
    status:          str             = "success",
) -> AuditLog:
    """Record a bounded, redacted audit event as described in Appendix A.5."""
    if isinstance(action, str):
        normalized = action.strip().lower()
        try:
            action = AuditActionEnum(normalized)
        except ValueError:
            pass

    ip = None
    browser = None
    os_name = None
    device  = None
    ua_raw  = None

    if request:
        ip = _safe_log_text(request.client.host if request.client else None, 50)
        ua_raw = _safe_log_text(request.headers.get("user-agent", ""), 512)
        browser, os_name, device = _parse_ua(ua_raw)

    log = AuditLog(
        user_id         = actor_id,
        role            = actor_role,
        module          = module,
        action          = action,
        affected_record = _safe_log_text(affected_record, 255),
        old_value       = json.dumps(_redact_structured_value(old_value)) if old_value else None,
        new_value       = json.dumps(_redact_structured_value(new_value)) if new_value else None,
        old_section_id  = old_section_id,
        new_section_id  = new_section_id,
        old_teacher_id  = old_teacher_id,
        new_teacher_id  = new_teacher_id,
        reason          = _safe_log_text(reason, 2000),
        ip_address      = ip,
        user_agent      = ua_raw,
        browser         = browser,
        os_name         = os_name,
        device_type     = device,
        status          = status,
    )

    return AuditLogRepository.create(db, log)


def record_access_denied(
    db: Session,
    *,
    request: Request,
    actor,
    required_role: RoleEnum,
) -> None:
    """Best-effort audit event that never changes the authorization result."""
    try:
        write_log(
            db,
            module="Authorization",
            action=AuditActionEnum.access_denied,
            actor_id=actor.id,
            actor_role=actor.role,
            affected_record=request.url.path,
            reason=f"{required_role.value} role required",
            request=request,
            status="failed",
        )
    except Exception:
        db.rollback()


def get_audit_logs(
    db:           Session,
    *,
    module:       Optional[str]           = None,
    action:       Optional[AuditActionEnum] = None,
    actor_role:   Optional[RoleEnum]       = None,
    date_from:    Optional[datetime]       = None,
    date_to:      Optional[datetime]       = None,
    search:       Optional[str]            = None,
    page:         int                      = 1,
    per_page:     int                      = 25,
):
    return AuditLogRepository.list_logs(
        db,
        module=module,
        action=action,
        actor_role=actor_role,
        date_from=date_from,
        date_to=date_to,
        search=search,
        page=page,
        per_page=per_page
    )
