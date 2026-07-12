from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Request
from models.accounts import Accounts
from models.student_profile import StudentProfile
from models.student_transfer_history import StudentTransferHistory
from models.student_assignment_history import StudentAssignmentHistory
from repositories.account_repository import AccountRepository
from repositories.section_repository import SectionRepository
from services.audit_service import write_log
from repositories.notification_repository import NotificationRepository
from utils.enum import AuditActionEnum, RoleEnum, NotificationCategoryEnum, NotificationPriorityEnum
from schemas.admin_schema import StudentTransferRequest
from typing import List, Optional

class StudentAdminService:
    @staticmethod
    def transfer_student(
        db: Session, 
        student_id: int, 
        data: StudentTransferRequest, 
        admin: Accounts, 
        request: Request
    ) -> Accounts:
        student = AccountRepository.get_by_id(db, student_id)
        if not student or student.role != RoleEnum.student:
            raise HTTPException(status_code=404, detail="Student not found")
            
        profile = student.student_profile
        if not profile:
            raise HTTPException(status_code=400, detail="Student profile not found")

        old_section_id = profile.section_id
        old_teacher_id = profile.assigned_section.teacher_id if profile.assigned_section else None
        
        # Look up target section
        if not data.to_section_id:
            raise HTTPException(status_code=400, detail="Target section is required for transfer")

        to_sec = SectionRepository.get_by_id(db, data.to_section_id)
        if not to_sec or to_sec.status != "active":
            raise HTTPException(status_code=400, detail="Target section not found or archived")

        # Check capacity
        student_count = db.query(StudentProfile).join(Accounts).filter(
            StudentProfile.section_id == to_sec.id,
            Accounts.account_status.in_(["active", "pending_approval"])
        ).count()
        if student_count >= to_sec.capacity:
            raise HTTPException(status_code=400, detail="Target section is already full.")

        target_teacher_id = to_sec.teacher_id
        if not target_teacher_id:
            raise HTTPException(status_code=400, detail="Target section does not have an assigned teacher")

        # Update profile
        profile.section_id = to_sec.id
        profile.grade_level_id = to_sec.grade_level_id
        
        # Log in Transfer History
        transfer = StudentTransferHistory(
            student_account_id=student.id,
            from_section_id=old_section_id,
            to_section_id=to_sec.id,
            from_teacher_id=old_teacher_id,
            to_teacher_id=target_teacher_id,
            transferred_by=admin.id,
            reason=data.reason
        )
        db.add(transfer)
        
        # Log in Assignment History
        assignment = StudentAssignmentHistory(
            student_account_id=student.id,
            event_type="transfer",
            section_id=to_sec.id,
            teacher_id=target_teacher_id,
            assigned_by=admin.id,
            notes=data.reason
        )
        db.add(assignment)
        
        db.commit()
        db.refresh(student)

        # Notify student & new teacher
        from models.notification import Notification
        NotificationRepository.create(db, Notification(
            recipient_id=student.id,
            title="Class Transfer Update",
            description=f"You have been transferred to section {to_sec.grade_level.name} - {to_sec.name}.",
            priority=NotificationPriorityEnum.medium,
            category=NotificationCategoryEnum.student,
            related_page="/student/dashboard"
        ))
        
        NotificationRepository.create(db, Notification(
            recipient_id=target_teacher_id,
            title="New Student Joined",
            description=f"Student {profile.name} was transferred into your class ({to_sec.name}).",
            priority=NotificationPriorityEnum.medium,
            category=NotificationCategoryEnum.section,
            related_page="/teacher/class"
        ))
        
        write_log(
            db,
            module="StudentManagement",
            action=AuditActionEnum.transferred,
            actor_id=admin.id,
            actor_role=admin.role,
            affected_record=f"Student {profile.name} transferred to {to_sec.name}",
            request=request
        )
        
        return student

    @staticmethod
    def get_transfer_history(db: Session, student_id: int) -> List[StudentTransferHistory]:
        return db.query(StudentTransferHistory).filter(StudentTransferHistory.student_account_id == student_id).all()

    @staticmethod
    def get_assignment_history(db: Session, student_id: int) -> List[StudentAssignmentHistory]:
        return db.query(StudentAssignmentHistory).filter(StudentAssignmentHistory.student_account_id == student_id).all()
