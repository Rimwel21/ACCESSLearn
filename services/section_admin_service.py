from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Request
from models.section import Section
from models.accounts import Accounts
from schemas.admin_schema import SectionCreate, SectionUpdate, SectionOut
from repositories.section_repository import SectionRepository
from repositories.account_repository import AccountRepository
from services.audit_service import write_log
from utils.enum import SectionStatusEnum, AuditActionEnum, RoleEnum
from typing import List, Tuple

class SectionAdminService:
    @staticmethod
    def create_section(db: Session, data: SectionCreate, admin: Accounts, request: Request) -> Section:
        section = Section(
            name=data.name,
            grade_level=data.grade_level,
            capacity=data.capacity,
            created_by=admin.id
        )
        new_section = SectionRepository.create(db, section)
        
        write_log(
            db,
            module="SectionManagement",
            action=AuditActionEnum.created,
            actor_id=admin.id,
            actor_role=admin.role,
            affected_record=f"Section {data.name} ({data.grade_level})",
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
            "grade_level": section.grade_level,
            "capacity": section.capacity
        }
        
        if data.name is not None:
            section.name = data.name
        if data.grade_level is not None:
            section.grade_level = data.grade_level
        if data.capacity is not None:
            section.capacity = data.capacity
            
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
        
        write_log(
            db,
            module="SectionManagement",
            action=AuditActionEnum.assigned,
            actor_id=admin.id,
            actor_role=admin.role,
            affected_record=f"Section #{section_id} assigned to Teacher #{teacher_id}",
            old_teacher_id=old_teacher_id,
            new_teacher_id=teacher_id,
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
            affected_record=f"Section #{section_id}",
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
            affected_record=f"Section #{section_id}",
            request=request
        )
        return updated
