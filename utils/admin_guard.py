"""
Admin guard dependency.

Raises HTTP 403 if the authenticated user is not an admin.
Use as: current_user: Accounts = Depends(require_admin)
"""
from fastapi import Depends, HTTPException, status
from models.accounts import Accounts
from utils.dependencies import get_current_user
from utils.enum import RoleEnum


def require_admin(current_user: Accounts = Depends(get_current_user)) -> Accounts:
    if current_user.role != RoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return current_user
