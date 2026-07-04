from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Request
from models.accounts import Accounts
from models.student_transfer_history import StudentTransferHistory
from models.student_assignment_history import StudentAssignmentHistory
from repositories.account_repository import AccountRepository
from repositories.section_repository import SectionRepository
from services.audit_service import write_log
from utils.enum import AuditActionEnum, RoleEnum
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
            
        # Placeholder for profile check and update
        # Assuming student_profile has section_id
        
        old_section_id = None # student.student_profile.section_id
        old_teacher_id = None # student.student_profile.teacher_id
        
        # Log in Transfer History
        transfer = StudentTransferHistory(
            student_account_id=student_id,
            from_section_id=old_section_id,
            to_section_id=data.to_section_id,
            from_teacher_id=old_teacher_id,
            to_teacher_id=data.to_teacher_id,
            transferred_by=admin.id,
            reason=data.reason
        )
        db.add(transfer)
        
        # Log in Assignment History
        assignment = StudentAssignmentHistory(
            student_account_id=student_id,
            event_type="transfer",
            section_id=data.to_section_id,
            teacher_id=data.to_teacher_id,
            assigned_by=admin.id,
            notes=data.reason
        )
        db.add(assignment)
        
        db.commit()
        
        write_log(
            db,
            module="StudentManagement",
            action=AuditActionEnum.transferred,
            actor_id=admin.id,
            actor_role=admin.role,
            affected_record=f"Student #{student_id}",
            old_section_id=old_section_id,
            new_section_id=data.to_section_id,
            old_teacher_id=old_teacher_id,
            new_teacher_id=data.to_teacher_id,
            reason=data.reason,
            request=request
        )
        
        return student

    @staticmethod
    def get_transfer_history(db: Session, student_id: int) -> List[StudentTransferHistory]:
        return db.query(StudentTransferHistory).filter(StudentTransferHistory.student_account_id == student_id).all()

    @staticmethod
    def get_assignment_history(db: Session, student_id: int) -> List[StudentAssignmentHistory]:
        return db.query(StudentAssignmentHistory).filter(StudentAssignmentHistory.student_account_id == student_id).all()
