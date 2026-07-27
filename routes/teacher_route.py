"""
Teacher API Routes.

All routes require a valid JWT with teacher role.
Sections are READ-ONLY for teachers — they cannot create or delete sections.
Teachers can:
  - View their assigned sections
  - View students in each section
  - Manage modules, quizzes, and activities within sections
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from utils.dependencies import get_db
from utils.teacher_guard import require_teacher
from models.accounts import Accounts
from models.section import Section
from models.student_profile import StudentProfile
from utils.enum import AccountStatusEnum

router = APIRouter(prefix="/teacher", tags=["Teacher"])


# ─── Pydantic Schemas ──────────────────────────────────────────────────────────

class TeacherSectionOut(BaseModel):
    id: int
    class_name: str       # kept for frontend compatibility → equals section.name
    subject: str | None = None
    grade_level: str      # grade level name
    grade_level_id: int
    section: str          # section name (same as class_name here)
    school_year: str | None = None
    student_count: int = 0
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class TeacherStudentOut(BaseModel):
    id: int                       # StudentProfile id
    account_id: int
    name: str
    username: str | None = None
    email: str | None = None
    grade_level: str | None = None
    section: str | None = None
    account_status: str
    created_at: str | None = None

    class Config:
        from_attributes = True


# ─── Sections ──────────────────────────────────────────────────────────────────

@router.get("/sections", response_model=List[TeacherSectionOut])
def get_teacher_sections(
    db: Session = Depends(get_db),
    teacher: Accounts = Depends(require_teacher)
):
    """Return all active sections assigned to this teacher."""
    sections = db.query(Section).filter(
        Section.teacher_id == teacher.id,
        Section.status == "active"
    ).all()

    result = []
    for sec in sections:
        count = db.query(StudentProfile).join(Accounts).filter(
            StudentProfile.section_id == sec.id,
            Accounts.account_status.in_([AccountStatusEnum.active, AccountStatusEnum.pending_approval])
        ).count()

        result.append(TeacherSectionOut(
            id=sec.id,
            class_name=sec.name,
            subject=sec.subject,
            grade_level=sec.grade_level.name if sec.grade_level else "",
            grade_level_id=sec.grade_level_id,
            section=sec.name,
            school_year=sec.school_year.name if sec.school_year else None,
            student_count=count,
            created_at=sec.created_at.isoformat(),
            updated_at=sec.updated_at.isoformat()
        ))
    return result


# Backwards-compatible alias: frontend calls /teacher/classes/
@router.get("/classes/", response_model=List[TeacherSectionOut])
def get_teacher_classes_compat(
    db: Session = Depends(get_db),
    teacher: Accounts = Depends(require_teacher)
):
    """Alias for /teacher/sections — maintained for frontend compatibility."""
    sections = db.query(Section).filter(
        Section.teacher_id == teacher.id,
        Section.status == "active"
    ).all()

    result = []
    for sec in sections:
        count = db.query(StudentProfile).join(Accounts).filter(
            StudentProfile.section_id == sec.id,
            Accounts.account_status.in_([AccountStatusEnum.active, AccountStatusEnum.pending_approval])
        ).count()

        result.append(TeacherSectionOut(
            id=sec.id,
            class_name=sec.name,
            subject=sec.subject,
            grade_level=sec.grade_level.name if sec.grade_level else "",
            grade_level_id=sec.grade_level_id,
            section=sec.name,
            school_year=sec.school_year.name if sec.school_year else None,
            student_count=count,
            created_at=sec.created_at.isoformat(),
            updated_at=sec.updated_at.isoformat()
        ))
    return result


# ─── Students in a Section ──────────────────────────────────────────────────────

@router.get("/sections/{section_id}/students", response_model=List[TeacherStudentOut])
def get_section_students(
    section_id: int,
    db: Session = Depends(get_db),
    teacher: Accounts = Depends(require_teacher)
):
    """Return approved/active students in the teacher's section."""
    sec = db.query(Section).filter(
        Section.id == section_id,
        Section.teacher_id == teacher.id
    ).first()
    if not sec:
        raise HTTPException(status_code=404, detail="Section not found or not assigned to you.")

    profiles = db.query(StudentProfile).join(Accounts).filter(
        StudentProfile.section_id == section_id,
        Accounts.account_status.in_([AccountStatusEnum.active])
    ).all()

    result = []
    for p in profiles:
        result.append(TeacherStudentOut(
            id=p.id,
            account_id=p.account_id,
            name=p.name,
            username=p.student_account.username if p.student_account else None,
            email=p.student_account.email if p.student_account else None,
            grade_level=p.assigned_grade.name if p.assigned_grade else None,
            section=p.assigned_section.name if p.assigned_section else None,
            account_status=p.student_account.account_status.value if p.student_account else "unknown",
            created_at=p.created_at.isoformat() if p.created_at else None
        ))
    return result


# Backwards-compatible alias: frontend calls /teacher/classes/{id}/students
@router.get("/classes/{class_id}/students", response_model=List[TeacherStudentOut])
def get_class_students_compat(
    class_id: int,
    db: Session = Depends(get_db),
    teacher: Accounts = Depends(require_teacher)
):
    """Alias for /teacher/sections/{id}/students — for frontend compatibility."""
    return get_section_students(class_id, db, teacher)


# ─── Available Sections & Selection ─────────────────────────────────────────────

@router.get("/sections/available", response_model=List[TeacherSectionOut])
def get_available_sections(
    db: Session = Depends(get_db),
    teacher: Accounts = Depends(require_teacher)
):
    """Return all active sections created by the administrator."""
    sections = db.query(Section).filter(
        Section.status == "active"
    ).all()

    result = []
    for sec in sections:
        count = db.query(StudentProfile).join(Accounts).filter(
            StudentProfile.section_id == sec.id,
            Accounts.account_status.in_([AccountStatusEnum.active, AccountStatusEnum.pending_approval])
        ).count()

        result.append(TeacherSectionOut(
            id=sec.id,
            class_name=sec.name,
            subject=sec.subject or "Science",
            grade_level=sec.grade_level.name if sec.grade_level else "",
            grade_level_id=sec.grade_level_id,
            section=sec.name,
            school_year=sec.school_year.name if sec.school_year else None,
            student_count=count,
            created_at=sec.created_at.isoformat(),
            updated_at=sec.updated_at.isoformat()
        ))
    return result


@router.post("/sections/{section_id}/select", response_model=TeacherSectionOut)
def select_section(
    section_id: int,
    db: Session = Depends(get_db),
    teacher: Accounts = Depends(require_teacher)
):
    """Select a section to manage."""
    sec = db.query(Section).filter(Section.id == section_id).first()
    if not sec:
        raise HTTPException(status_code=404, detail="Section not found.")

    # Assign this section to the teacher
    sec.teacher_id = teacher.id
    db.commit()
    db.refresh(sec)

    count = db.query(StudentProfile).join(Accounts).filter(
        StudentProfile.section_id == sec.id,
        Accounts.account_status.in_([AccountStatusEnum.active, AccountStatusEnum.pending_approval])
    ).count()

    from services.audit_service import write_log
    from utils.enum import AuditActionEnum
    write_log(
        db,
        module="ClassManagement",
        action=AuditActionEnum.section_update,
        actor_id=teacher.id,
        actor_role=teacher.role,
        affected_record=f"Section {sec.name}",
        new_value={"teacher_id": teacher.id}
    )

    return TeacherSectionOut(
        id=sec.id,
        class_name=sec.name,
        subject=sec.subject or "Science",
        grade_level=sec.grade_level.name if sec.grade_level else "",
        grade_level_id=sec.grade_level_id,
        section=sec.name,
        school_year=sec.school_year.name if sec.school_year else None,
        student_count=count,
        created_at=sec.created_at.isoformat(),
        updated_at=sec.updated_at.isoformat()
    )


@router.post("/sections/{section_id}/unselect", response_model=TeacherSectionOut)
def unselect_section(
    section_id: int,
    db: Session = Depends(get_db),
    teacher: Accounts = Depends(require_teacher)
):
    """Unselect a section (unassign teacher)."""
    sec = db.query(Section).filter(Section.id == section_id, Section.teacher_id == teacher.id).first()
    if not sec:
        raise HTTPException(status_code=404, detail="Section not found or not assigned to you.")

    sec.teacher_id = None
    db.commit()
    db.refresh(sec)

    count = db.query(StudentProfile).join(Accounts).filter(
        StudentProfile.section_id == sec.id,
        Accounts.account_status.in_([AccountStatusEnum.active, AccountStatusEnum.pending_approval])
    ).count()

    from services.audit_service import write_log
    from utils.enum import AuditActionEnum
    write_log(
        db,
        module="ClassManagement",
        action=AuditActionEnum.section_update,
        actor_id=teacher.id,
        actor_role=teacher.role,
        affected_record=f"Section {sec.name}",
        old_value={"teacher_id": teacher.id},
        new_value={"teacher_id": None}
    )

    return TeacherSectionOut(
        id=sec.id,
        class_name=sec.name,
        subject=sec.subject or "Science",
        grade_level=sec.grade_level.name if sec.grade_level else "",
        grade_level_id=sec.grade_level_id,
        section=sec.name,
        school_year=sec.school_year.name if sec.school_year else None,
        student_count=count,
        created_at=sec.created_at.isoformat(),
        updated_at=sec.updated_at.isoformat()
    )
