from fastapi import HTTPException, status, Depends, Request
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from models.accounts import Accounts
from models.HI_sections import HI_SECTIONS
from models.student_profile import StudentProfile
from models.teacher_class import TeacherClass
from schemas.create_section_schema import SectionCreate, SectionUpdate
from utils.enum import AuditActionEnum, RoleEnum
from services.academic_service import get_grade_level_or_404
from services.audit_service import write_log

def _get_admin_account(current_user: Accounts):
    if current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    
def create_section(request: Request, section: SectionCreate, db: Session, current_user: Accounts):
    _get_admin_account(current_user)

    get_grade_level_or_404(section.grade_level_id, db)

    exiting_section = db.query(HI_SECTIONS).filter(
        func.lower(HI_SECTIONS.name) == section.name.lower(),
        HI_SECTIONS.grade_level_id == section.grade_level_id,
    ).first()

    if exiting_section:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This section already exists for the selected grade level.")

    new_section = HI_SECTIONS(
        name=section.name,
        grade_level_id=section.grade_level_id
    )

    db.add(new_section)
    db.commit()
    db.refresh(new_section)

    write_log(
        db,
        module="Section Management",
        action=AuditActionEnum.created,
        actor_id=current_user.id,
        actor_role=current_user.role,
        affected_record=f"Section #{new_section.id}: {new_section.name}",
        new_value={"name": new_section.name, "grade_level_id": new_section.grade_level_id},
        new_section_id=new_section.id,
        request=request,
    )

    result = (
        db.query(HI_SECTIONS)
        .options(joinedload(HI_SECTIONS.grade_level))
        .filter(HI_SECTIONS.id == new_section.id)
        .first()
    )

    return result


def update_section(request: Request, section_id: int, section: SectionUpdate, db: Session, current_user: Accounts):
    _get_admin_account(current_user)

    existing_section = db.query(HI_SECTIONS).filter(HI_SECTIONS.id == section_id).first()
    if not existing_section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")

    duplicate_section = db.query(HI_SECTIONS).filter(
        HI_SECTIONS.id != section_id,
        func.lower(HI_SECTIONS.name) == section.name.lower(),
        HI_SECTIONS.grade_level_id == existing_section.grade_level_id,
    ).first()

    if duplicate_section:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This section already exists for the selected grade level.")

    old_name = existing_section.name
    existing_section.name = section.name
    db.commit()
    db.refresh(existing_section)

    write_log(
        db,
        module="Section Management",
        action=AuditActionEnum.updated,
        actor_id=current_user.id,
        actor_role=current_user.role,
        affected_record=f"Section #{existing_section.id}: {existing_section.name}",
        old_value={"name": old_name, "grade_level_id": existing_section.grade_level_id},
        new_value={"name": existing_section.name, "grade_level_id": existing_section.grade_level_id},
        old_section_id=existing_section.id,
        new_section_id=existing_section.id,
        request=request,
    )

    return existing_section


def delete_section(request: Request, section_id: int, db: Session, current_user: Accounts):
    _get_admin_account(current_user)

    section = db.query(HI_SECTIONS).filter(HI_SECTIONS.id == section_id).first()
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")

    student_count = db.query(StudentProfile).filter(StudentProfile.section_id == section_id).count()
    teacher_class_count = db.query(TeacherClass).filter(TeacherClass.section_id == section_id).count()

    if student_count or teacher_class_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Cannot delete this section while it has "
                f"{student_count} student{'s' if student_count != 1 else ''} and "
                f"{teacher_class_count} teacher class{'es' if teacher_class_count != 1 else ''}. "
                "Transfer or remove them first."
            )
        )

    deleted_snapshot = {"name": section.name, "grade_level_id": section.grade_level_id}
    affected_record = f"Section #{section.id}: {section.name}"
    try:
        db.delete(section)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This section is already used by students or teacher classes and cannot be deleted."
        )

    write_log(
        db,
        module="Section Management",
        action=AuditActionEnum.hard_deleted,
        actor_id=current_user.id,
        actor_role=current_user.role,
        affected_record=affected_record,
        old_value=deleted_snapshot,
        request=request,
    )

    return {"message": "Section deleted successfully"}
