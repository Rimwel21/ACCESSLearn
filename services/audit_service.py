"""
Audit Log Service.

Provides write_log() for any service to call, plus paginated query
with rich filtering and export support.
"""
from __future__ import annotations
import json
from datetime import datetime
from typing import Optional
from fastapi import Request
from sqlalchemy.orm import Session

from models.audit_log import AuditLog
from repositories.audit_log_repository import AuditLogRepository
from utils.enum import AuditActionEnum, RoleEnum


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


def write_log(
    db:              Session,
    *,
    module:          str,
    action:          AuditActionEnum,
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
    ip = None
    browser = None
    os_name = None
    device  = None
    ua_raw  = None

    if request:
        ip = request.client.host if request.client else None
        ua_raw = request.headers.get("user-agent", "")
        browser, os_name, device = _parse_ua(ua_raw)

    log = AuditLog(
        user_id         = actor_id,
        role            = actor_role,
        module          = module,
        action          = action,
        affected_record = affected_record,
        old_value       = json.dumps(old_value)   if old_value else None,
        new_value       = json.dumps(new_value)   if new_value else None,
        old_section_id  = old_section_id,
        new_section_id  = new_section_id,
        old_teacher_id  = old_teacher_id,
        new_teacher_id  = new_teacher_id,
        reason          = reason,
        ip_address      = ip,
        user_agent      = ua_raw,
        browser         = browser,
        os_name         = os_name,
        device_type     = device,
        status          = status,
    )

    return AuditLogRepository.create(db, log)


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
