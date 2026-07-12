from sqlalchemy.orm import Session
from schemas.admin_schema import AdminDashboardStats, SectionCapacityInfo
from repositories.account_repository import AccountRepository
from repositories.invitation_repository import InvitationRepository
from repositories.section_repository import SectionRepository
from repositories.notification_repository import NotificationRepository
from repositories.audit_log_repository import AuditLogRepository
from utils.enum import AccountStatusEnum, RoleEnum, SectionStatusEnum
from datetime import datetime, timedelta, timezone

class DashboardService:
    @staticmethod
    def get_stats(db: Session, admin_id: int) -> AdminDashboardStats:
        # Teacher Stats
        total_teachers = AccountRepository.count_by_status(db, role=RoleEnum.teacher)
        pending_activation = AccountRepository.count_by_status(db, role=RoleEnum.teacher, status=AccountStatusEnum.pending_activation)
        waiting_assignment = AccountRepository.count_by_status(db, role=RoleEnum.teacher, status=AccountStatusEnum.waiting_assignment)
        active_teachers = AccountRepository.count_by_status(db, role=RoleEnum.teacher, status=AccountStatusEnum.active)
        inactive_teachers = AccountRepository.count_by_status(db, role=RoleEnum.teacher, status=AccountStatusEnum.inactive)
        archived_teachers = AccountRepository.count_by_status(db, role=RoleEnum.teacher, status=AccountStatusEnum.archived)

        # Student Stats
        total_students = AccountRepository.count_by_status(db, role=RoleEnum.student)
        active_students = AccountRepository.count_by_status(db, role=RoleEnum.student, status=AccountStatusEnum.active)
        inactive_students = AccountRepository.count_by_status(db, role=RoleEnum.student, status=AccountStatusEnum.inactive)
        archived_students = AccountRepository.count_by_status(db, role=RoleEnum.student, status=AccountStatusEnum.archived)
        
        # Placeholder for students without teacher (requires checking student_profile -> section -> teacher)
        students_without_teacher = 0 

        # Section Stats
        total_sections = SectionRepository.count_sections(db)
        sections_without_teacher = SectionRepository.count_sections(db, without_teacher=True)
        
        # Sections near capacity (mock logic for now, should query section model)
        # Fetching all active sections and filtering
        _, all_sections = SectionRepository.list_sections(db, status=SectionStatusEnum.active, per_page=100)
        sections_near_capacity = []
        for sec in all_sections:
            count = 0 # SectionRepository.get_student_count(db, sec.id)
            pct = (count / sec.capacity) * 100 if sec.capacity > 0 else 0
            if pct >= 80:
                sections_near_capacity.append(SectionCapacityInfo(
                    section_id=sec.id,
                    section_name=sec.name,
                    grade_level=sec.grade_level,
                    capacity=sec.capacity,
                    current_count=count,
                    available_slots=sec.capacity - count,
                    capacity_pct=pct,
                    capacity_status="Critical" if pct >= 95 else "Warning"
                ))

        # Recent Activity
        now = datetime.now(timezone.utc)
        # Placeholder for recent logins/failed logins (requires audit log check)
        recent_login_count = 0 
        failed_login_count_24h = 0
        recent_transfers = 0
        
        pending_invitations = InvitationRepository.count_pending(db)
        unread_notifications = NotificationRepository.unread_count(db, admin_id)

        return AdminDashboardStats(
            total_teachers=total_teachers,
            pending_activation=pending_activation,
            waiting_assignment=waiting_assignment,
            active_teachers=active_teachers,
            inactive_teachers=inactive_teachers,
            archived_teachers=archived_teachers,
            total_students=total_students,
            active_students=active_students,
            inactive_students=inactive_students,
            archived_students=archived_students,
            students_without_teacher=students_without_teacher,
            total_sections=total_sections,
            sections_without_teacher=sections_without_teacher,
            sections_near_capacity=sections_near_capacity,
            recent_login_count=recent_login_count,
            failed_login_count_24h=failed_login_count_24h,
            recent_transfers=recent_transfers,
            pending_invitations=pending_invitations,
            unread_notifications=unread_notifications
        )
