"""Student role guard for learner-only routes."""

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from models.accounts import Accounts
from services.audit_service import record_access_denied
from utils.dependencies import get_current_user, get_db
from utils.enum import RoleEnum


def require_student(
    request: Request,
    current_user: Accounts = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Accounts:
    if current_user.role != RoleEnum.student:
        record_access_denied(db, request=request, actor=current_user, required_role=RoleEnum.student)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required.",
        )
    return current_user
