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
    grade_1 = "grade_1"
    grade_2 = "grade_2"
    grade_3 = "grade_3"
    grade_4 = "grade_4"
    grade_5 = "grade_5"
    grade_6 = "grade_6"

class FileCategory(str, Enum):
    PROFILE_IMAGE = "PROFILE_IMAGE"
    LEARNING_MATERIAL = "LEARNING_MATERIAL"

class VerificationStatus(str, Enum):
    pending = "pending"
    verified = "verified"
    blocked = "blocked"

class AccountStatusEnum(str, Enum):
    pending_activation = "pending_activation"
    waiting_assignment = "waiting_assignment"
    active = "active"
    inactive = "inactive"
    archived = "archived"
    suspended = "suspended"

class SectionStatusEnum(str, Enum):
    active = "active"
    inactive = "inactive"
    archived = "archived"

class AuditActionEnum(str, Enum):
    created = "created"
    updated = "updated"
    assigned = "assigned"
    archived = "archived"
    restored = "restored"
    transferred = "transferred"
    invited = "invited"
    invitation_resent = "invitation_resent"
    invitation_cancelled = "invitation_cancelled"
    activated = "activated"
    deactivated = "deactivated"
    hard_deleted = "hard_deleted"
    bulk_action = "bulk_action"

class NotificationCategoryEnum(str, Enum):
    student = "student"
    section = "section"
    teacher = "teacher"
    system = "system"

class NotificationPriorityEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class InvitationStatusEnum(str, Enum):
    pending = "pending"
    accepted = "accepted"
    resent = "resent"
    cancelled = "cancelled"

class ReportTypeEnum(str, Enum):
    audit_report = "audit_report"
    account_status = "account_status"

class BulkActionEnum(str, Enum):
    activate = "activate"
    deactivate = "deactivate"
    archive = "archive"
    restore = "restore"
    delete = "delete"

