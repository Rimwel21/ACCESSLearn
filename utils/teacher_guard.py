"""
Teacher guard dependency.

Raises HTTP 403 if the authenticated user is not a teacher.
Use as: current_user: Accounts = Depends(require_teacher)
"""
from fastapi import Depends, HTTPException, status
from models.accounts import Accounts
from utils.dependencies import get_current_user
from utils.enum import RoleEnum


def require_teacher(current_user: Accounts = Depends(get_current_user)) -> Accounts:
    if current_user.role != RoleEnum.teacher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher access required.",
        )
    return current_user
