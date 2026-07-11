from enum import Enum

# Role Enum (Student, Teacher, Admin):
class RoleEnum(str, Enum):
    student = "student"
    teacher = "teacher"
    admin = "admin"

# student type enum:
class StudentType(str, Enum):
    regular = "regular"
    HI = "hearing impaired"

class UserSex(str, Enum):
    Male = "Male"
    Female = "Female"

class GradeLevel(str, Enum):
    kindergarten = "kindergarten"
    grade_1 = "grade_1"
    grade_2 = "grade_2"
    grade_3 = "grade_3"
    grade_4 = "grade_4"
    grade_5 = "grade_5"
    grade_6 = "grade_6"

class FileCategory(str, Enum):
    PROFILE_IMAGE = "PROFILE_IMAGE"
    LEARNING_MATERIAL = "LEARNING_MATERIAL"

# ─── Admin-specific enums ──────────────────────────────────────────────────────

class AccountStatusEnum(str, Enum):
    """Full lifecycle for teacher and student accounts."""
    pending_activation  = "pending_activation"   # invitation sent, not yet verified
    waiting_assignment  = "waiting_assignment"    # email verified + password set, awaiting grade/section
    pending_approval    = "pending_approval"      # student registered, waiting for admin approval
    active              = "active"
    inactive            = "inactive"
    archived            = "archived"
    suspended           = "suspended"

class InvitationStatusEnum(str, Enum):
    pending   = "pending"
    accepted  = "accepted"
    expired   = "expired"
    cancelled = "cancelled"
    resent    = "resent"

class SectionStatusEnum(str, Enum):
    active   = "active"
    archived = "archived"

class NotificationPriorityEnum(str, Enum):
    low      = "low"
    medium   = "medium"
    high     = "high"
    critical = "critical"

class NotificationCategoryEnum(str, Enum):
    system   = "system"
    teacher  = "teacher"
    student  = "student"
    section  = "section"
    security = "security"
    account  = "account"
    learning = "learning"
    quiz     = "quiz"
    assignment = "assignment"

class AuditActionEnum(str, Enum):
    created            = "created"
    updated            = "updated"
    deleted            = "deleted"
    archived           = "archived"
    restored           = "restored"
    hard_deleted       = "hard_deleted"
    activated          = "activated"
    deactivated        = "deactivated"
    invited            = "invited"
    invitation_resent  = "invitation_resent"
    invitation_cancelled = "invitation_cancelled"
    transferred        = "transferred"
    assigned           = "assigned"
    login              = "login"
    logout             = "logout"
    login_failed       = "login_failed"
    password_reset     = "password_reset"
    password_changed   = "password_changed"
    bulk_action        = "bulk_action"
    report_generated   = "report_generated"

class BulkActionEnum(str, Enum):
    activate   = "activate"
    deactivate = "deactivate"
    archive    = "archive"
    restore    = "restore"
    delete     = "delete"
    resend_invitation = "resend_invitation"

class ReportTypeEnum(str, Enum):
    teacher_performance = "teacher_performance"
    student_progress    = "student_progress"
    section_distribution = "section_distribution"
    quiz_analytics      = "quiz_analytics"
    learning_material   = "learning_material"
    activity_report     = "activity_report"
    login_report        = "login_report"
    notification_report = "notification_report"
    audit_report        = "audit_report"
    account_status      = "account_status"
    archive_report      = "archive_report"
    password_reset      = "password_reset"
    transfer_report     = "transfer_report"

