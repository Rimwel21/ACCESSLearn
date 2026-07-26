from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session
from models.accounts import Accounts
from models.audit_log import AuditLog
from schemas.accounts_schema import PendingTeacherResponse
from utils.enum import AccountStatusEnum, RoleEnum
from utils.dependencies import get_current_user, get_db
from services.admin_approval_service import admin_approval, admin_block, teachers_pending_account

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.patch("/teachers/{teacher_id}/approve")
def admin_approval_routes(teacher_id: int, current_user: Accounts = Depends(get_current_user), db: Session = Depends(get_db)):
    return admin_approval(teacher_id=teacher_id, current_user=current_user, db=db)

@router.patch("/teachers/{teacher_id}/block")
def admin_block_routes(teacher_id: int, current_user: Accounts = Depends(get_current_user), db: Session = Depends(get_db)):
    return admin_block(teacher_id=teacher_id, current_user=current_user, db=db)

@router.get("/teachers/pendings", response_model=list[PendingTeacherResponse])
def teachers_pending_account_routes(current_user: Accounts = Depends(get_current_user), db: Session = Depends(get_db)):
    return teachers_pending_account(current_user=current_user, db=db)


def _require_admin(current_user: Accounts):
    if current_user.role != RoleEnum.admin:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")


@router.get("/accounts")
def list_admin_accounts(
    role: Optional[RoleEnum] = None,
    status: Optional[AccountStatusEnum] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: Accounts = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(current_user)
    query = db.query(Accounts)

    if role:
        query = query.filter(Accounts.role == role)
    if status:
        query = query.filter(Accounts.account_status == status)
    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(Accounts.email.ilike(pattern), Accounts.username.ilike(pattern)))

    total = query.count()
    items = (
        query.order_by(Accounts.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "items": [
            {
                "id": account.id,
                "full_name": account.username or account.email or f"Account #{account.id}",
                "email": account.email,
                "role": account.role,
                "account_status": account.account_status,
                "created_at": account.created_at,
            }
            for account in items
        ],
    }


@router.get("/audit-logs")
def list_admin_audit_logs(
    actor_role: Optional[RoleEnum] = None,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    current_user: Accounts = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(current_user)
    query = db.query(AuditLog)

    if actor_role:
        query = query.filter(AuditLog.role == actor_role)
    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(
            AuditLog.module.ilike(pattern),
            AuditLog.affected_record.ilike(pattern),
            AuditLog.ip_address.ilike(pattern),
        ))
    if date_from:
        query = query.filter(AuditLog.created_at >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.filter(AuditLog.created_at <= datetime.fromisoformat(date_to))

    total = query.count()
    items = (
        query.order_by(desc(AuditLog.created_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "items": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "role": log.role,
                "module": log.module,
                "action": log.action,
                "affected_record": log.affected_record,
                "reason": log.reason,
                "ip_address": log.ip_address,
                "browser": log.browser,
                "os_name": log.os_name,
                "device_type": log.device_type,
                "location": log.location,
                "status": log.status,
                "created_at": log.created_at,
            }
            for log in items
        ],
    }
