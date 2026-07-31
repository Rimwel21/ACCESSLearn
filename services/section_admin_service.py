from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Request
from models.section import Section
from models.accounts import Accounts
from models.grade_levels import GradeLevels
from models.school_year import SchoolYear
from models.teacher_assignment_history import TeacherAssignmentHistory
from models.student_profile import StudentProfile
from schemas.admin_schema import (
    SectionCreate, SectionUpdate, 
    GradeLevelCreate, GradeLevelUpdate, 
    SchoolYearCreate, SchoolYearUpdate
)
from repositories.section_repository import SectionRepository
from repositories.account_repository import AccountRepository
from services.audit_service import write_log
from repositories.notification_repository import NotificationRepository
from utils.enum import SectionStatusEnum, AuditActionEnum, RoleEnum, NotificationCategoryEnum, NotificationPriorityEnum
from typing import List, Tuple, Optional

class SectionAdminService:
    # ─── Grade Level CRUD ──────────────────────────────────────────────────────────
    @staticmethod
    def create_grade_level(db: Session, data: GradeLevelCreate, admin: Accounts, request: Request) -> GradeLevels:
        existing = db.query(GradeLevels).filter(GradeLevels.name == data.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Grade level already exists")
        
        grade = GradeLevels(name=data.name, status=SectionStatusEnum.active)
        db.add(grade)
        db.commit()
        db.refresh(grade)

        write_log(
            db, module="GradeLevelManagement", action=AuditActionEnum.created,
            actor_id=admin.id, actor_role=admin.role,
            affected_record=f"Grade Level: {grade.name}", request=request
        )
        return grade

    @staticmethod
    def update_grade_level(db: Session, grade_id: int, data: GradeLevelUpdate, admin: Accounts, request: Request) -> GradeLevels:
        grade = db.query(GradeLevels).filter(GradeLevels.id == grade_id).first()
        if not grade:
            raise HTTPException(status_code=404, detail="Grade level not found")
        
        if data.name is not None and data.name != grade.name:
            existing = db.query(GradeLevels).filter(GradeLevels.name == data.name).first()
            if existing:
                raise HTTPException(status_code=400, detail="Grade level name already exists")
            grade.name = data.name

        if data.status is not None:
            grade.status = data.status

        db.commit()
        db.refresh(grade)

        write_log(
            db, module="GradeLevelManagement", action=AuditActionEnum.updated,
            actor_id=admin.id, actor_role=admin.role,
            affected_record=f"Grade Level #{grade_id}", request=request
        )
        return grade

    @staticmethod
    def archive_grade_level(db: Session, grade_id: int, admin: Accounts, request: Request) -> GradeLevels:
        grade = db.query(GradeLevels).filter(GradeLevels.id == grade_id).first()
        if not grade:
            raise HTTPException(status_code=404, detail="Grade level not found")
        
        grade.status = SectionStatusEnum.archived
        db.commit()
        db.refresh(grade)

        write_log(
            db, module="GradeLevelManagement", action=AuditActionEnum.archived,
            actor_id=admin.id, actor_role=admin.role,
            affected_record=f"Archived Grade Level: {grade.name}", request=request
        )
        return grade

    @staticmethod
    def restore_grade_level(db: Session, grade_id: int, admin: Accounts, request: Request) -> GradeLevels:
        grade = db.query(GradeLevels).filter(GradeLevels.id == grade_id).first()
        if not grade:
            raise HTTPException(status_code=404, detail="Grade level not found")
        
        grade.status = SectionStatusEnum.active
        db.commit()
        db.refresh(grade)

        write_log(
            db, module="GradeLevelManagement", action=AuditActionEnum.restored,
            actor_id=admin.id, actor_role=admin.role,
            affected_record=f"Restored Grade Level: {grade.name}", request=request
        )
        return grade


    # ─── School Year CRUD ──────────────────────────────────────────────────────────
    @staticmethod
    def create_school_year(db: Session, data: SchoolYearCreate, admin: Accounts, request: Request) -> SchoolYear:
        existing = db.query(SchoolYear).filter(SchoolYear.name == data.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="School Year already exists")

        sy = SchoolYear(name=data.name, status=SectionStatusEnum.active, is_current=False)
        db.add(sy)
        db.commit()
        db.refresh(sy)

        write_log(
            db, module="SchoolYearManagement", action=AuditActionEnum.created,
            actor_id=admin.id, actor_role=admin.role,
            affected_record=f"School Year: {sy.name}", request=request
        )
        return sy

    @staticmethod
    def update_school_year(db: Session, sy_id: int, data: SchoolYearUpdate, admin: Accounts, request: Request) -> SchoolYear:
        sy = db.query(SchoolYear).filter(SchoolYear.id == sy_id).first()
        if not sy:
            raise HTTPException(status_code=404, detail="School Year not found")

        if data.name is not None and data.name != sy.name:
            existing = db.query(SchoolYear).filter(SchoolYear.name == data.name).first()
            if existing:
                raise HTTPException(status_code=400, detail="School Year name already exists")
            sy.name = data.name

        if data.is_current is not None:
            if data.is_current:
                # Reset all others to current = False
                db.query(SchoolYear).update({"is_current": False})
            sy.is_current = data.is_current

        if data.status is not None:
            sy.status = data.status

        db.commit()
        db.refresh(sy)

        write_log(
            db, module="SchoolYearManagement", action=AuditActionEnum.updated,
            actor_id=admin.id, actor_role=admin.role,
            affected_record=f"School Year #{sy_id}", request=request
        )
        return sy


    # ─── Section CRUD ──────────────────────────────────────────────────────────────
    @staticmethod
    def list_sections(
        db: Session,
        grade_level_id: Optional[int] = None,
        school_year_id: Optional[int] = None,
        status: Optional[SectionStatusEnum] = None,
        teacher_id: Optional[int] = None,
        page: int = 1,
        per_page: int = 20,
    ):
        return SectionRepository.list_sections(
            db,
            grade_level_id=grade_level_id,
            school_year_id=school_year_id,
            status=status,
            teacher_id=teacher_id,
            page=page,
            per_page=per_page,
        )

    @staticmethod
    def create_section(db: Session, data: SectionCreate, admin: Accounts, request: Request) -> Section:
        # Check duplicate
        existing = db.query(Section).filter(
            Section.name == data.name, 
            Section.grade_level_id == data.grade_level_id,
            Section.school_year_id == data.school_year_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Section already exists in this Grade Level and School Year.")

        grade = db.query(GradeLevels).filter(GradeLevels.id == data.grade_level_id).first()
        if not grade:
            raise HTTPException(status_code=400, detail="Invalid Grade Level ID")

        sy = db.query(SchoolYear).filter(SchoolYear.id == data.school_year_id).first()
        if not sy:
            raise HTTPException(status_code=400, detail="Invalid School Year ID")

        section = Section(
            name=data.name,
            grade_level_id=data.grade_level_id,
            school_year_id=data.school_year_id,
            capacity=data.capacity,
            subject=data.subject,
            created_by=admin.id
        )
        new_section = SectionRepository.create(db, section)
        
        write_log(
            db,
            module="SectionManagement",
            action=AuditActionEnum.created,
            actor_id=admin.id,
            actor_role=admin.role,
            affected_record=f"Section {data.name} ({grade.name})",
            new_value=data.model_dump(),
            request=request
        )
        return new_section

    @staticmethod
    def update_section(db: Session, section_id: int, data: SectionUpdate, admin: Accounts, request: Request) -> Section:
        section = SectionRepository.get_by_id(db, section_id)
        if not section:
            raise HTTPException(status_code=404, detail="Section not found")
        
        old_val = {
            "name": section.name,
            "grade_level_id": section.grade_level_id,
            "school_year_id": section.school_year_id,
            "capacity": section.capacity,
            "subject": section.subject
        }
        
        name_val = data.name if data.name is not None else section.name
        grade_val = data.grade_level_id if data.grade_level_id is not None else section.grade_level_id
        sy_val = data.school_year_id if data.school_year_id is not None else section.school_year_id

        if name_val != section.name or grade_val != section.grade_level_id or sy_val != section.school_year_id:
            existing = db.query(Section).filter(
                Section.name == name_val,
                Section.grade_level_id == grade_val,
                Section.school_year_id == sy_val,
                Section.id != section_id
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="Another section with this name already exists in this Grade Level and School Year")

        if data.name is not None:
            section.name = data.name
        if data.grade_level_id is not None:
            section.grade_level_id = data.grade_level_id
        if data.school_year_id is not None:
            section.school_year_id = data.school_year_id
        if data.capacity is not None:
            section.capacity = data.capacity
        if data.subject is not None:
            section.subject = data.subject
        if data.status is not None:
            section.status = data.status
            
        updated = SectionRepository.update(db, section)
        
        write_log(
            db,
            module="SectionManagement",
            action=AuditActionEnum.updated,
            actor_id=admin.id,
            actor_role=admin.role,
            affected_record=f"Section #{section_id}",
            old_value=old_val,
            new_value=data.model_dump(exclude_unset=True),
            request=request
        )
        return updated

    @staticmethod
    def assign_teacher(db: Session, section_id: int, teacher_id: int, admin: Accounts, request: Request) -> Section:
        section = SectionRepository.get_by_id(db, section_id)
        if not section:
            raise HTTPException(status_code=404, detail="Section not found")
            
        teacher = AccountRepository.get_by_id(db, teacher_id)
        if not teacher or teacher.role != RoleEnum.teacher:
            raise HTTPException(status_code=400, detail="Invalid teacher ID")
            
        old_teacher_id = section.teacher_id
        section.teacher_id = teacher_id
        updated = SectionRepository.update(db, section)

        # Log assignment history
        history = TeacherAssignmentHistory(
            section_id=section_id,
            previous_teacher_id=old_teacher_id,
            new_teacher_id=teacher_id,
            assigned_by=admin.id
        )
        db.add(history)
        db.commit()

        # Send notification to teacher
        from models.notification import Notification
        notif = Notification(
            recipient_id=teacher_id,
            title="Class Assignment Update",
            description=f"You have been assigned as teacher for {section.grade_level.name} - {section.name}.",
            priority=NotificationPriorityEnum.high,
            category=NotificationCategoryEnum.section,
            related_page="/teacher/class"
        )
        NotificationRepository.create(db, notif)
        
        write_log(
            db,
            module="SectionManagement",
            action=AuditActionEnum.assigned,
            actor_id=admin.id,
            actor_role=admin.role,
            affected_record=f"Section #{section_id} assigned to Teacher #{teacher_id}",
            request=request
        )
        return updated

    @staticmethod
    def archive_section(db: Session, section_id: int, admin: Accounts, request: Request) -> Section:
        section = SectionRepository.get_by_id(db, section_id)
        if not section:
            raise HTTPException(status_code=404, detail="Section not found")
            
        section.status = SectionStatusEnum.archived
        updated = SectionRepository.update(db, section)
        
        write_log(
            db,
            module="SectionManagement",
            action=AuditActionEnum.archived,
            actor_id=admin.id,
            actor_role=admin.role,
            affected_record=f"Archived Section {section.name}",
            request=request
        )
        return updated

    @staticmethod
    def restore_section(db: Session, section_id: int, admin: Accounts, request: Request) -> Section:
        section = SectionRepository.get_by_id(db, section_id)
        if not section:
            raise HTTPException(status_code=404, detail="Section not found")
            
        section.status = SectionStatusEnum.active
        updated = SectionRepository.update(db, section)
        
        write_log(
            db,
            module="SectionManagement",
            action=AuditActionEnum.restored,
            actor_id=admin.id,
            actor_role=admin.role,
            affected_record=f"Restored Section {section.name}",
            request=request
        )
        return updated
