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

def get_section_students(section_id: int, db: Session, current_user: Accounts):
    """Return all students enrolled in the given hi_section."""
    _get_admin_account(current_user)

    section = db.query(HI_SECTIONS).filter(HI_SECTIONS.id == section_id).first()
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")

    students = (
        db.query(StudentProfile)
        .options(
            joinedload(StudentProfile.grade_level),
            joinedload(StudentProfile.section),
            joinedload(StudentProfile.student_account),
        )
        .filter(StudentProfile.section_id == section_id)
        .order_by(StudentProfile.name.asc())
        .all()
    )

    result = []
    for s in students:
        result.append({
            "id": s.id,
            "account_id": s.account_id,
            "name": s.name,
            "student_type": s.student_type,
            "grade_level_id": s.grade_level_id,
            "grade_level_name": s.grade_level.name if s.grade_level else None,
            "section_id": s.section_id,
            "section_name": s.section.name if s.section else None,
            "account_status": s.student_account.account_status if s.student_account else None,
        })
    return result
def transfer_student_hi_section(
    request: Request,
    student_id: int,
    grade_level_id: int,
    section_id: int,
    db: Session,
    current_user: Accounts,
):
    """Transfer a student (identified by student_profile.id) to a new hi_section."""
    _get_admin_account(current_user)

    from models.grade_levels import GradeLevels

    student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    # Validate target grade level
    target_grade = db.query(GradeLevels).filter(GradeLevels.id == grade_level_id).first()
    if not target_grade:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target grade level not found")

    # Validate target section
    target_section = db.query(HI_SECTIONS).filter(HI_SECTIONS.id == section_id).first()
    if not target_section:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target section not found")

    # Ensure section belongs to the selected grade level
    if target_section.grade_level_id != grade_level_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected section does not belong to the selected grade level",
        )

    # Prevent no-op transfer
    if student.grade_level_id == grade_level_id and student.section_id == section_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student is already in the selected grade level and section",
        )

    old_grade_id = student.grade_level_id
    old_section_id = student.section_id

    student.grade_level_id = grade_level_id
    student.section_id = section_id
    db.commit()
    db.refresh(student)

    write_log(
        db,
        module="Section Management",
        action=AuditActionEnum.transferred,
        actor_id=current_user.id,
        actor_role=current_user.role,
        affected_record=f"Student #{student_id}: {student.name} transferred to Section #{section_id}: {target_section.name}",
        old_value={"grade_level_id": old_grade_id, "section_id": old_section_id},
        new_value={"grade_level_id": grade_level_id, "section_id": section_id},
        request=request,
    )

    return {
        "success": True,
        "message": "Student transferred successfully.",
        "student_id": student_id,
        "new_grade_level_id": grade_level_id,
        "new_section_id": section_id,
    }


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


def assign_teacher_to_section(
    request: Request,
    section_id: int,
    teacher_id: int,
    db: Session,
    current_user: Accounts,
):
    _get_admin_account(current_user)

    from models.accounts import Accounts as AccountsModel
    from utils.enum import RoleEnum

    section = db.query(HI_SECTIONS).filter(HI_SECTIONS.id == section_id).first()
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")

    teacher = db.query(AccountsModel).filter(
        AccountsModel.id == teacher_id,
        AccountsModel.role == RoleEnum.teacher,
    ).first()
    if not teacher:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid teacher or teacher not found")

    section.teacher_id = teacher_id
    db.commit()
    db.refresh(section)

    write_log(
        db,
        module="Section Management",
        action=AuditActionEnum.assigned,
        actor_id=current_user.id,
        actor_role=current_user.role,
        affected_record=f"Teacher #{teacher_id} assigned to Section #{section_id}: {section.name}",
        request=request,
    )

    return section


def unassign_teacher_from_section(
    request: Request,
    section_id: int,
    db: Session,
    current_user: Accounts,
):
    _get_admin_account(current_user)

    section = db.query(HI_SECTIONS).filter(HI_SECTIONS.id == section_id).first()
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")

    old_teacher_id = section.teacher_id
    section.teacher_id = None
    db.commit()
    db.refresh(section)

    write_log(
        db,
        module="Section Management",
        action=AuditActionEnum.updated,
        actor_id=current_user.id,
        actor_role=current_user.role,
        affected_record=f"Teacher #{old_teacher_id} removed from Section #{section_id}: {section.name}",
        request=request,
    )

    return {"message": "Teacher unassigned successfully"}


def list_sections_with_teacher(db: Session):
    """Return all hi_sections with their assigned teacher info for admin panel."""
    from sqlalchemy.orm import joinedload
    sections = (
        db.query(HI_SECTIONS)
        .options(joinedload(HI_SECTIONS.grade_level), joinedload(HI_SECTIONS.teacher))
        .order_by(HI_SECTIONS.grade_level_id.asc(), HI_SECTIONS.name.asc())
        .all()
    )
    result = []
    for sec in sections:
        teacher_name = None
        teacher_email = None
        if sec.teacher:
            tp = getattr(sec.teacher, "teacher_profile", None)
            teacher_name  = tp.name  if tp and hasattr(tp, "name")  else None
            teacher_email = sec.teacher.email
        result.append({
            "id": sec.id,
            "name": sec.name,
            "grade_level_id": sec.grade_level_id,
            "grade_level_name": sec.grade_level.name if sec.grade_level else None,
            "teacher_id": sec.teacher_id,
            "teacher_name": teacher_name or teacher_email,
            "student_count": len(sec.students) if sec.students else 0,
        })
    return result
