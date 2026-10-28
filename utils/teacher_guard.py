"""
Teacher guard dependency.

Raises HTTP 403 if the authenticated user is not a teacher.
Use as: current_user: Accounts = Depends(require_teacher)
"""
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from models.accounts import Accounts
from services.audit_service import record_access_denied
from utils.dependencies import get_current_user, get_db
from utils.enum import RoleEnum


def require_teacher(request: Request, current_user: Accounts = Depends(get_current_user), db: Session = Depends(get_db)) -> Accounts:
    if current_user.role != RoleEnum.teacher:
        record_access_denied(db, request=request, actor=current_user, required_role=RoleEnum.teacher)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher access required.",
        )
    return current_user
