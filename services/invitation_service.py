"""
Invitation Service.

Handles teacher invitation creation, token generation, resend, and cancellation.
No SMTP configured — tokens are returned in the response so the admin can
copy/share the link manually. SMTP wiring is a TODO comment.
"""
from __future__ import annotations
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session

from models.teacher_invitation import TeacherInvitation
from models.accounts import Accounts
from repositories.invitation_repository import InvitationRepository
from utils.enum import InvitationStatusEnum
from services.audit_service import write_log
from services.notification_service import create_notification
from utils.enum import AuditActionEnum, NotificationCategoryEnum, NotificationPriorityEnum

INVITE_EXPIRE_HOURS = 72  # invitations valid for 72 hours


def _generate_token() -> str:
    return secrets.token_urlsafe(48)


def send_teacher_invitation(
    db:         Session,
    *,
    full_name:  str,
    email:      str,
    contact_no: Optional[str],
    admin:      Accounts,
    request:    Optional[Request] = None,
) -> TeacherInvitation:
    # Check for existing active invitation
    existing = InvitationRepository.get_pending_by_email(db, email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A pending invitation already exists for {email}. Cancel it first or resend.",
        )

    token = _generate_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=INVITE_EXPIRE_HOURS)

    invitation = TeacherInvitation(
        full_name  = full_name,
        email      = email,
        contact_no = contact_no,
        token      = token,
        status     = InvitationStatusEnum.pending,
        invited_by = admin.id,
        expires_at = expires_at,
    )
    new_inv = InvitationRepository.create(db, invitation)

    # TODO: Send activation email via SMTP / SendGrid / Supabase Auth
    # For now, the token is returned so admin can share the link manually.

    write_log(
        db,
        module          = "TeacherManagement",
        action          = AuditActionEnum.invited,
        actor_id        = admin.id,
        actor_role      = admin.role,
        affected_record = f"Invitation #{new_inv.id} → {email}",
        new_value       = {"email": email, "full_name": full_name},
        request         = request,
    )

    create_notification(
        db,
        recipient_id = admin.id,
        icon         = "✉️",
        title        = "Teacher Invitation Sent",
        description  = f"Invitation sent to {full_name} ({email}). Expires in 72 hours.",
        category     = NotificationCategoryEnum.teacher,
        priority     = NotificationPriorityEnum.medium,
        related_page = "/admin/teachers",
    )

    return new_inv


def resend_invitation(
    db:            Session,
    invitation_id: int,
    *,
    admin:         Accounts,
    note:          Optional[str] = None,
    request:       Optional[Request] = None,
) -> TeacherInvitation:
    inv = InvitationRepository.get_by_id(db, invitation_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invitation not found.")
    if inv.status == InvitationStatusEnum.accepted:
        raise HTTPException(status_code=400, detail="Invitation already accepted.")
    if inv.status == InvitationStatusEnum.cancelled:
        raise HTTPException(status_code=400, detail="Invitation was cancelled. Create a new one.")

    inv.token      = _generate_token()
    inv.expires_at = datetime.now(timezone.utc) + timedelta(hours=INVITE_EXPIRE_HOURS)
    inv.status     = InvitationStatusEnum.resent
    inv.resend_note = note
    updated_inv = InvitationRepository.update(db, inv)

    write_log(
        db,
        module          = "TeacherManagement",
        action          = AuditActionEnum.invitation_resent,
        actor_id        = admin.id,
        actor_role      = admin.role,
        affected_record = f"Invitation #{inv.id} → {inv.email}",
        request         = request,
    )

    return updated_inv


def cancel_invitation(
    db:            Session,
    invitation_id: int,
    *,
    admin:         Accounts,
    request:       Optional[Request] = None,
) -> TeacherInvitation:
    inv = InvitationRepository.get_by_id(db, invitation_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invitation not found.")
    if inv.status == InvitationStatusEnum.accepted:
        raise HTTPException(status_code=400, detail="Cannot cancel an accepted invitation.")

    inv.status = InvitationStatusEnum.cancelled
    updated_inv = InvitationRepository.update(db, inv)

    write_log(
        db,
        module          = "TeacherManagement",
        action          = AuditActionEnum.invitation_cancelled,
        actor_id        = admin.id,
        actor_role      = admin.role,
        affected_record = f"Invitation #{inv.id} → {inv.email}",
        request         = request,
    )

    return updated_inv


def list_invitations(
    db:        Session,
    *,
    status_f:  Optional[InvitationStatusEnum] = None,
    search:    Optional[str]                  = None,
    page:      int                            = 1,
    per_page:  int                            = 20,
):
    return InvitationRepository.list_invitations(
        db, status=status_f, search=search, page=page, per_page=per_page
    )
