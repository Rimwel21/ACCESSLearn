"""
Account Admin Service.

Manages account lifecycle (activate, deactivate, archive, restore, hard delete)
and list/search/filter/bulk actions on accounts.
"""
from __future__ import annotations
from typing import Optional, List
from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session

from models.accounts import Accounts
from repositories.account_repository import AccountRepository
from utils.enum import AccountStatusEnum, RoleEnum, AuditActionEnum, BulkActionEnum
from services.audit_service import write_log

def list_accounts(
    db:             Session,
    *,
    role:           Optional[RoleEnum]          = None,
    account_status: Optional[AccountStatusEnum] = None,
    search:         Optional[str]               = None,
    page:           int                         = 1,
    per_page:       int                         = 20,
):
    return AccountRepository.list_accounts(
        db, role=role, account_status=account_status, search=search, page=page, per_page=per_page
    )

def change_account_status(
    db:                Session,
    account_id:        int,
    new_status:        AccountStatusEnum,
    *,
    admin:             Accounts,
    reason:            Optional[str] = None,
    request:           Optional[Request] = None,
) -> Accounts:
    account = AccountRepository.get_by_id(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found.")
    if account.role == RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Cannot modify another admin account.")

    old_status = account.account_status
    updated_account = AccountRepository.update_status(db, account, new_status)

    action_map = {
        AccountStatusEnum.active:   AuditActionEnum.activated,
        AccountStatusEnum.inactive: AuditActionEnum.deactivated,
        AccountStatusEnum.archived: AuditActionEnum.archived,
    }
    action = action_map.get(new_status, AuditActionEnum.updated)

    write_log(
        db,
        module          = "AccountManagement",
        action          = action,
        actor_id        = admin.id,
        actor_role      = admin.role,
        affected_record = f"Account #{account_id} ({account.email or account.username})",
        old_value       = {"account_status": old_status},
        new_value       = {"account_status": new_status},
        reason          = reason,
        request         = request,
    )

    return updated_account

def hard_delete_account(
    db:         Session,
    account_id: int,
    *,
    admin:      Accounts,
    request:    Optional[Request] = None,
) -> None:
    account = AccountRepository.get_by_id(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found.")
    if account.account_status != AccountStatusEnum.archived:
        raise HTTPException(
            status_code=400,
            detail="Account must be archived before permanent deletion.",
        )
    if account.role == RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Cannot delete an admin account.")

    identifier = account.email or account.username or f"#{account_id}"

    write_log(
        db,
        module          = "AccountManagement",
        action          = AuditActionEnum.hard_deleted,
        actor_id        = admin.id,
        actor_role      = admin.role,
        affected_record = f"Account #{account_id} ({identifier})",
        old_value       = {"role": account.role, "status": account.account_status},
        request         = request,
    )

    AccountRepository.hard_delete(db, account)

def bulk_action(
    db:          Session,
    account_ids: List[int],
    action:      BulkActionEnum,
    *,
    admin:       Accounts,
    reason:      Optional[str] = None,
    request:     Optional[Request] = None,
) -> int:
    status_map = {
        BulkActionEnum.activate:   AccountStatusEnum.active,
        BulkActionEnum.deactivate: AccountStatusEnum.inactive,
        BulkActionEnum.archive:    AccountStatusEnum.archived,
        BulkActionEnum.restore:    AccountStatusEnum.active,
    }

    count = 0
    if action == BulkActionEnum.delete:
        count = AccountRepository.bulk_hard_delete(db, account_ids)
    else:
        new_stat = status_map.get(action)
        if new_stat:
            count = AccountRepository.bulk_status_update(db, account_ids, new_stat)

    write_log(
        db,
        module          = "AccountManagement",
        action          = AuditActionEnum.bulk_action,
        actor_id        = admin.id,
        actor_role      = admin.role,
        affected_record = f"Bulk {action} on {count} account(s)",
        new_value       = {"action": action, "ids": account_ids},
        reason          = reason,
        request         = request,
    )

    return count
