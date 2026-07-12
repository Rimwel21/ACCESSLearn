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
        AccountStatusEnum.suspended: AuditActionEnum.deactivated,
    }
    action = action_map.get(new_status, AuditActionEnum.updated)

    # Status Notification Triggers for Student Approval
    if account.role == RoleEnum.student and new_status == AccountStatusEnum.active and old_status != AccountStatusEnum.active:
        from repositories.notification_repository import NotificationRepository
        from models.student_profile import StudentProfile
        from models.section import Section
        from models.notification import Notification
        from utils.enum import NotificationCategoryEnum, NotificationPriorityEnum
        from repositories.section_repository import SectionRepository
        
        profile = db.query(StudentProfile).filter(StudentProfile.account_id == account.id).first()
        if profile and profile.section_id:
            sec = db.query(Section).filter(Section.id == profile.section_id).first()
            if sec:
                # 1. Student Notification: Approved
                NotificationRepository.create(db, Notification(
                    recipient_id=account.id,
                    title="Registration Approved",
                    description=f"Welcome! Your registration for {sec.grade_level.name if sec.grade_level else ''} - {sec.name} has been approved.",
                    priority=NotificationPriorityEnum.medium,
                    category=NotificationCategoryEnum.student,
                    related_page="/student/dashboard"
                ))
                
                # 2. Student Notification: Teacher Assigned
                if sec.teacher_id:
                    t_name = sec.teacher.teacher_profile.name if (sec.teacher and sec.teacher.teacher_profile) else (sec.teacher.email if sec.teacher else "")
                    NotificationRepository.create(db, Notification(
                        recipient_id=account.id,
                        title="Teacher Assigned",
                        description=f"Teacher {t_name} has been assigned to your section.",
                        priority=NotificationPriorityEnum.low,
                        category=NotificationCategoryEnum.student,
                        related_page="/student/dashboard"
                    ))
                    
                    # 3. Teacher Notification: Student Joined
                    NotificationRepository.create(db, Notification(
                        recipient_id=sec.teacher_id,
                        title="New Student Joined",
                        description=f"Student {profile.name} has been approved and joined your class ({sec.name}).",
                        priority=NotificationPriorityEnum.medium,
                        category=NotificationCategoryEnum.section,
                        related_page="/teacher/class"
                    ))
                
                # 4. Admin capacity warning
                stud_count = SectionRepository.get_student_count(db, sec.id)
                if stud_count >= sec.capacity:
                    NotificationRepository.create(db, Notification(
                        recipient_id=admin.id,
                        title="Section Capacity Reached",
                        description=f"Section {sec.grade_level.name if sec.grade_level else ''} - {sec.name} is now at full capacity ({sec.capacity}/{sec.capacity}).",
                        priority=NotificationPriorityEnum.high,
                        category=NotificationCategoryEnum.system,
                        related_page="/admin/sections"
                    ))

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
