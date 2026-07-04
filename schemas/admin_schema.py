"""
Pydantic schemas for the Admin module.
Covers: invitations, account management, sections, dashboard stats,
audit logs, notifications, reports, bulk actions, and student transfers.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr, Field, field_validator

from utils.enum import (
    AccountStatusEnum,
    InvitationStatusEnum,
    RoleEnum,
    SectionStatusEnum,
    GradeLevel,
    NotificationPriorityEnum,
    NotificationCategoryEnum,
    AuditActionEnum,
    BulkActionEnum,
    ReportTypeEnum,
)


# ─── Invitation ────────────────────────────────────────────────────────────────

class TeacherInviteCreate(BaseModel):
    full_name:  str = Field(..., min_length=2, max_length=100)
    email:      EmailStr
    contact_no: Optional[str] = Field(None, max_length=25)

class TeacherInviteOut(BaseModel):
    id:         int
    full_name:  str
    email:      str
    contact_no: Optional[str]
    status:     InvitationStatusEnum
    expires_at: datetime
    created_at: datetime
    updated_at: datetime
    account_id: Optional[int]

    class Config:
        from_attributes = True

class ResendInviteRequest(BaseModel):
    note: Optional[str] = Field(None, max_length=500)


# ─── Account Status ────────────────────────────────────────────────────────────

class AccountStatusUpdate(BaseModel):
    account_status: AccountStatusEnum
    reason:         Optional[str] = Field(None, max_length=500)

class AccountListOut(BaseModel):
    id:             int
    username:       Optional[str]
    email:          Optional[str]
    role:           RoleEnum
    account_status: AccountStatusEnum
    name:           Optional[str]        = None   # from profile
    contact_no:     Optional[str]        = None
    grade_level:    Optional[str]        = None
    section_name:   Optional[str]        = None
    created_at:     datetime
    updated_at:     datetime

    class Config:
        from_attributes = True

class HardDeleteRequest(BaseModel):
    """Client must send confirmation = 'DELETE' to proceed with permanent removal."""
    confirmation: str = Field(..., pattern="^DELETE$")


# ─── Bulk Actions ──────────────────────────────────────────────────────────────

class BulkActionRequest(BaseModel):
    account_ids: List[int] = Field(..., min_length=1)
    action:      BulkActionEnum
    reason:      Optional[str] = Field(None, max_length=500)


# ─── Section ───────────────────────────────────────────────────────────────────

class SectionCreate(BaseModel):
    name:        str         = Field(..., min_length=1, max_length=100)
    grade_level: GradeLevel
    capacity:    int         = Field(40, ge=1, le=200)

class SectionUpdate(BaseModel):
    name:        Optional[str]         = None
    grade_level: Optional[GradeLevel]  = None
    capacity:    Optional[int]         = Field(None, ge=1, le=200)

class SectionAssignTeacher(BaseModel):
    teacher_id: int

class SectionOut(BaseModel):
    id:              int
    name:            str
    grade_level:     GradeLevel
    capacity:        int
    status:          SectionStatusEnum
    teacher_id:      Optional[int]
    teacher_name:    Optional[str]   = None
    current_count:   int             = 0      # computed by service
    available_slots: int             = 0
    capacity_pct:    float           = 0.0
    capacity_status: str             = "Normal"  # Normal | Warning | Critical | Full
    created_at:      datetime
    updated_at:      datetime

    class Config:
        from_attributes = True


# ─── Student Transfer ──────────────────────────────────────────────────────────

class StudentTransferRequest(BaseModel):
    to_section_id:  Optional[int] = None
    to_teacher_id:  Optional[int] = None
    reason:         Optional[str] = Field(None, max_length=500)

class TransferHistoryOut(BaseModel):
    id:                    int
    student_account_id:    int
    from_section_id:       Optional[int]
    to_section_id:         Optional[int]
    from_teacher_id:       Optional[int]
    to_teacher_id:         Optional[int]
    reason:                Optional[str]
    created_at:            datetime

    class Config:
        from_attributes = True

class AssignmentHistoryOut(BaseModel):
    id:                 int
    student_account_id: int
    event_type:         str
    section_id:         Optional[int]
    teacher_id:         Optional[int]
    grade_level:        Optional[str]
    notes:              Optional[str]
    created_at:         datetime

    class Config:
        from_attributes = True


# ─── Dashboard Stats ───────────────────────────────────────────────────────────

class SectionCapacityInfo(BaseModel):
    section_id:      int
    section_name:    str
    grade_level:     str
    capacity:        int
    current_count:   int
    available_slots: int
    capacity_pct:    float
    capacity_status: str

class AdminDashboardStats(BaseModel):
    # Teacher lifecycle counts
    total_teachers:             int = 0
    pending_activation:         int = 0
    waiting_assignment:         int = 0
    active_teachers:            int = 0
    inactive_teachers:          int = 0
    archived_teachers:          int = 0

    # Student counts
    total_students:             int = 0
    active_students:            int = 0
    inactive_students:          int = 0
    archived_students:          int = 0
    students_without_teacher:   int = 0

    # Section counts
    total_sections:             int = 0
    sections_without_teacher:   int = 0
    sections_near_capacity:     List[SectionCapacityInfo] = []

    # Activity indicators
    recent_login_count:         int = 0
    failed_login_count_24h:     int = 0
    recent_transfers:           int = 0
    pending_invitations:        int = 0
    unread_notifications:       int = 0


# ─── Audit Log ─────────────────────────────────────────────────────────────────

class AuditLogOut(BaseModel):
    id:              int
    user_id:         Optional[int]
    role:            Optional[RoleEnum]
    module:          str
    action:          AuditActionEnum
    affected_record: Optional[str]
    old_value:       Optional[str]
    new_value:       Optional[str]
    reason:          Optional[str]
    ip_address:      Optional[str]
    browser:         Optional[str]
    os_name:         Optional[str]
    device_type:     Optional[str]
    location:        Optional[str]
    status:          str
    created_at:      datetime

    class Config:
        from_attributes = True


# ─── Notification ──────────────────────────────────────────────────────────────

class NotificationCreate(BaseModel):
    recipient_id:    int
    icon:            Optional[str]                    = None
    title:           str                              = Field(..., max_length=255)
    description:     Optional[str]                   = None
    priority:        NotificationPriorityEnum         = NotificationPriorityEnum.medium
    category:        NotificationCategoryEnum         = NotificationCategoryEnum.system
    related_user_id: Optional[int]                   = None
    related_page:    Optional[str]                   = None

class NotificationOut(BaseModel):
    id:              int
    icon:            Optional[str]
    title:           str
    description:     Optional[str]
    priority:        NotificationPriorityEnum
    category:        NotificationCategoryEnum
    related_user_id: Optional[int]
    related_page:    Optional[str]
    is_read:         bool
    created_at:      datetime

    class Config:
        from_attributes = True


# ─── Reports ───────────────────────────────────────────────────────────────────

class ReportRequest(BaseModel):
    report_type: ReportTypeEnum
    date_from:   Optional[datetime] = None
    date_to:     Optional[datetime] = None
    grade_level: Optional[str]      = None
    section_id:  Optional[int]      = None
    teacher_id:  Optional[int]      = None

class ReportOut(BaseModel):
    report_type: str
    generated_at: datetime
    filters_applied: dict
    row_count: int
    data: List[dict]


# ─── Pagination wrapper ────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    total:    int
    page:     int
    per_page: int
    items:    List[Any]
