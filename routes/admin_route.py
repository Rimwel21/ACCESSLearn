from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from database.connection import get_db
from models.accounts import Accounts
from utils.admin_guard import require_admin
from schemas.admin_schema import (
    AdminDashboardStats,
    AccountListOut,
    AccountStatusUpdate,
    BulkActionRequest,
    TeacherInviteCreate,
    TeacherInviteOut,
    ResendInviteRequest,
    SectionCreate,
    SectionUpdate,
    SectionOut,
    StudentTransferRequest,
    AuditLogOut,
    NotificationOut,
    ReportRequest,
    ReportOut,
    PaginatedResponse,
    TransferHistoryOut,
    AssignmentHistoryOut
)
from services.dashboard_service import DashboardService
from services.account_admin_service import list_accounts, change_account_status, hard_delete_account, bulk_action
from services.invitation_service import send_teacher_invitation, list_invitations, resend_invitation, cancel_invitation
from services.section_admin_service import SectionAdminService
from services.student_admin_service import StudentAdminService
from services.audit_service import get_audit_logs
from services.notification_service import get_notifications, mark_read, mark_all_read, delete_notification, delete_all_notifications
from services.report_service import ReportService
from utils.enum import RoleEnum, AccountStatusEnum, InvitationStatusEnum, AuditActionEnum, SectionStatusEnum, GradeLevel

router = APIRouter(prefix="/admin", tags=["Admin"])

# ─── Dashboard ────────────────────────────────────────────────────────────────

@router.get("/dashboard", response_model=AdminDashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    admin: Accounts = Depends(require_admin)
):
    return DashboardService.get_stats(db, admin.id)


# ─── Account Management ────────────────────────────────────────────────────────

@router.get("/accounts", response_model=PaginatedResponse)
def get_accounts(
    role: Optional[RoleEnum] = None,
    status: Optional[AccountStatusEnum] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: Accounts = Depends(require_admin)
):
    total, items = list_accounts(db, role=role, account_status=status, search=search, page=page, per_page=per_page)
    return PaginatedResponse(total=total, page=page, per_page=per_page, items=items)

@router.patch("/accounts/{account_id}/status", response_model=AccountListOut)
def update_account_status(
    account_id: int,
    data: AccountStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: Accounts = Depends(require_admin)
):
    return change_account_status(db, account_id, data.account_status, admin=admin, reason=data.reason, request=request)

@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account_permanently(
    account_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: Accounts = Depends(require_admin)
):
    hard_delete_account(db, account_id, admin=admin, request=request)
    return

@router.post("/accounts/bulk-action")
def perform_bulk_action(
    data: BulkActionRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: Accounts = Depends(require_admin)
):
    count = bulk_action(db, data.account_ids, data.action, admin=admin, reason=data.reason, request=request)
    return {"message": f"Successfully performed {data.action} on {count} accounts."}


# ─── Teacher Management ────────────────────────────────────────────────────────

@router.post("/teachers/invite", response_model=TeacherInviteOut)
def invite_teacher(
    data: TeacherInviteCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: Accounts = Depends(require_admin)
):
    return send_teacher_invitation(db, full_name=data.full_name, email=data.email, contact_no=data.contact_no, admin=admin, request=request)

@router.get("/teachers/invitations", response_model=PaginatedResponse)
def get_teacher_invitations(
    status: Optional[InvitationStatusEnum] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: Accounts = Depends(require_admin)
):
    total, items = list_invitations(db, status_f=status, search=search, page=page, per_page=per_page)
    return PaginatedResponse(total=total, page=page, per_page=per_page, items=items)

@router.post("/teachers/invitations/{invitation_id}/resend", response_model=TeacherInviteOut)
def resend_teacher_invite(
    invitation_id: int,
    data: ResendInviteRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: Accounts = Depends(require_admin)
):
    return resend_invitation(db, invitation_id, admin=admin, note=data.note, request=request)

@router.delete("/teachers/invitations/{invitation_id}/cancel", response_model=TeacherInviteOut)
def cancel_teacher_invite(
    invitation_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: Accounts = Depends(require_admin)
):
    return cancel_invitation(db, invitation_id, admin=admin, request=request)


# ─── Section Management ────────────────────────────────────────────────────────

@router.post("/sections", response_model=SectionOut)
def create_new_section(
    data: SectionCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: Accounts = Depends(require_admin)
):
    return SectionAdminService.create_section(db, data, admin, request)

@router.get("/sections", response_model=PaginatedResponse)
def get_sections(
    grade_level: Optional[GradeLevel] = None,
    status: Optional[SectionStatusEnum] = None,
    teacher_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: Accounts = Depends(require_admin)
):
    total, items = SectionAdminService.list_sections(db, grade_level=grade_level, status=status, teacher_id=teacher_id, page=page, per_page=per_page)
    # Mapping items to include counts if necessary
    return PaginatedResponse(total=total, page=page, per_page=per_page, items=items)

@router.patch("/sections/{section_id}", response_model=SectionOut)
def update_section_info(
    section_id: int,
    data: SectionUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: Accounts = Depends(require_admin)
):
    return SectionAdminService.update_section(db, section_id, data, admin, request)

@router.patch("/sections/{section_id}/assign-teacher", response_model=SectionOut)
def assign_teacher_to_section(
    section_id: int,
    teacher_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: Accounts = Depends(require_admin)
):
    return SectionAdminService.assign_teacher(db, section_id, teacher_id, admin, request)

@router.post("/sections/{section_id}/archive", response_model=SectionOut)
def archive_section(
    section_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: Accounts = Depends(require_admin)
):
    return SectionAdminService.archive_section(db, section_id, admin, request)


# ─── Student Management ────────────────────────────────────────────────────────

@router.patch("/students/{student_id}/transfer")
def transfer_student_record(
    student_id: int,
    data: StudentTransferRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: Accounts = Depends(require_admin)
):
    return StudentAdminService.transfer_student(db, student_id, data, admin, request)

@router.get("/students/{student_id}/transfer-history", response_model=List[TransferHistoryOut])
def get_student_transfer_history(
    student_id: int,
    db: Session = Depends(get_db),
    admin: Accounts = Depends(require_admin)
):
    return StudentAdminService.get_transfer_history(db, student_id)

@router.get("/students/{student_id}/assignment-history", response_model=List[AssignmentHistoryOut])
def get_student_assignment_history(
    student_id: int,
    db: Session = Depends(get_db),
    admin: Accounts = Depends(require_admin)
):
    return StudentAdminService.get_assignment_history(db, student_id)


# ─── Audit Logs ────────────────────────────────────────────────────────────────

@router.get("/audit-logs", response_model=PaginatedResponse)
def list_system_audit_logs(
    module: Optional[str] = None,
    action: Optional[AuditActionEnum] = None,
    actor_role: Optional[RoleEnum] = None,
    date_from: Optional[str] = None, # datetime string
    date_to: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: Accounts = Depends(require_admin)
):
    # Parsing dates if provided
    d_from = None
    if date_from:
        d_from = datetime.fromisoformat(date_from)
    d_to = None
    if date_to:
        d_to = datetime.fromisoformat(date_to)

    total, items = get_audit_logs(db, module=module, action=action, actor_role=actor_role, date_from=d_from, date_to=d_to, search=search, page=page, per_page=per_page)
    return PaginatedResponse(total=total, page=page, per_page=per_page, items=items)


# ─── Notifications ─────────────────────────────────────────────────────────────

@router.get("/notifications", response_model=PaginatedResponse)
def get_admin_notifications(
    unread_only: bool = False,
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: Accounts = Depends(require_admin)
):
    total, items = get_notifications(db, admin.id, unread_only=unread_only, page=page, per_page=per_page)
    return PaginatedResponse(total=total, page=page, per_page=per_page, items=items)

@router.patch("/notifications/{notification_id}/read", response_model=NotificationOut)
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    admin: Accounts = Depends(require_admin)
):
    notif = mark_read(db, notification_id, admin.id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notif

@router.delete("/notifications/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    admin: Accounts = Depends(require_admin)
):
    if not delete_notification(db, notification_id, admin.id):
        raise HTTPException(status_code=404, detail="Notification not found")
    return


# ─── Reports ───────────────────────────────────────────────────────────────────

@router.post("/reports", response_model=ReportOut)
def generate_admin_report(
    data: ReportRequest,
    db: Session = Depends(get_db),
    admin: Accounts = Depends(require_admin)
):
    return ReportService.generate_report(db, data)
