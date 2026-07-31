from fastapi import APIRouter, Request, Depends, Query
from sqlalchemy.orm import Session
from models.accounts import Accounts
from services.admin_create_section_service import (
    create_section,
    delete_section,
    update_section,
    assign_teacher_to_section,
    unassign_teacher_from_section,
    list_sections_with_teacher,
    get_section_students,
    transfer_student_hi_section,
)
from schemas.create_section_schema import SectionCreate, SectionOut, SectionUpdate
from utils.dependencies import get_db, get_current_user

router = APIRouter(prefix="/section", tags=["Section"])


@router.post("/create/admin", response_model=SectionOut)
def create_section_route(
    request: Request,
    section: SectionCreate,
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user),
):
    return create_section(request=request, section=section, db=db, current_user=current_user)


@router.patch("/{section_id}", response_model=SectionOut)
def update_section_route(
    section_id: int,
    request: Request,
    section: SectionUpdate,
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user),
):
    return update_section(request=request, section_id=section_id, section=section, db=db, current_user=current_user)


@router.delete("/{section_id}")
def delete_section_route(
    section_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user),
):
    return delete_section(request=request, section_id=section_id, db=db, current_user=current_user)


# ── Teacher Assignment ────────────────────────────────────────────────────────

@router.patch("/{section_id}/assign-teacher")
def assign_teacher_route(
    section_id: int,
    request: Request,
    teacher_id: int = Query(..., description="ID of the teacher account to assign"),
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user),
):
    """Admin assigns a Science Teacher to an existing hi_section."""
    section = assign_teacher_to_section(
        request=request,
        section_id=section_id,
        teacher_id=teacher_id,
        db=db,
        current_user=current_user,
    )
    return {
        "id": section.id,
        "name": section.name,
        "grade_level_id": section.grade_level_id,
        "teacher_id": section.teacher_id,
        "message": "Teacher assigned successfully",
    }


@router.delete("/{section_id}/unassign-teacher")
def unassign_teacher_route(
    section_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user),
):
    """Admin removes the teacher assignment from an existing hi_section."""
    return unassign_teacher_from_section(
        request=request,
        section_id=section_id,
        db=db,
        current_user=current_user,
    )


@router.get("/with-teacher")
def list_sections_with_teacher_route(
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user),
):
    """Return all hi_sections with assigned teacher info, for admin management panel."""
    from services.admin_create_section_service import _get_admin_account
    _get_admin_account(current_user)
    return list_sections_with_teacher(db)


# ── Student Roster & Transfer ─────────────────────────────────────────────────

from pydantic import BaseModel as _BaseModel

class TransferBody(_BaseModel):
    grade_level_id: int
    section_id: int


@router.get("/{section_id}/students")
def get_section_students_route(
    section_id: int,
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user),
):
    """Return all students enrolled in the given hi_section (Admin only)."""
    return get_section_students(section_id=section_id, db=db, current_user=current_user)


@router.patch("/transfer-student/{student_id}")
def transfer_student_route(
    student_id: int,
    request: Request,
    body: TransferBody,
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user),
):
    """Transfer a student to a new grade level and section (Admin only)."""
    return transfer_student_hi_section(
        request=request,
        student_id=student_id,
        grade_level_id=body.grade_level_id,
        section_id=body.section_id,
        db=db,
        current_user=current_user,
    )
