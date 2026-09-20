from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from limiter import limiter
from models.HI_sections import HI_SECTIONS
from models.accounts import Accounts
from models.grade_levels import GradeLevels
from models.student_profile import StudentProfile
from models.teacher_class import TeacherClass
from schemas.teacher_class_schema import TeacherClassOut
from services.academic_service import ALLOWED_GRADE_NAMES, get_grade_level_or_404
from utils.dependencies import get_current_user, get_db
from utils.enum import AccountStatusEnum, RoleEnum
from utils.utc_now import utc_now


router = APIRouter(prefix="/teacher/sections", tags=["Teacher Sections"])


def _ensure_teacher(current_user: Accounts):
    if current_user.role != RoleEnum.teacher:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher only")


def _student_count(section_id: int, db: Session) -> int:
    return (
        db.query(StudentProfile)
        .join(Accounts)
        .filter(
            StudentProfile.section_id == section_id,
            Accounts.account_status.in_([AccountStatusEnum.active, AccountStatusEnum.pending_approval]),
        )
        .count()
    )


def _section_payload(section: HI_SECTIONS, teacher_id: int, db: Session) -> dict:
    timestamp = utc_now()
    return {
        "id": section.id,
        "teacher_id": teacher_id,
        "class_name": f"{section.grade_level.name if section.grade_level else 'Grade'} - {section.name}",
        "subject": "Science",
        "grade_levels": {
            "id": section.grade_level_id,
            "name": section.grade_level.name if section.grade_level else "",
        },
        "sections": {
            "id": section.id,
            "name": section.name,
            "grade_level_id": section.grade_level_id,
        },
        "school_year": None,
        "student_count": _student_count(section.id, db),
        "created_at": timestamp,
        "updated_at": timestamp,
    }


def _teacher_class_for_section(section: HI_SECTIONS, teacher_id: int, db: Session) -> TeacherClass:
    existing = (
        db.query(TeacherClass)
        .options(joinedload(TeacherClass.grade_levels), joinedload(TeacherClass.sections))
        .filter(
            TeacherClass.teacher_id == teacher_id,
            TeacherClass.grade_level_id == section.grade_level_id,
            TeacherClass.section_id == section.id,
            TeacherClass.subject == "Science",
        )
        .first()
    )
    if existing:
        existing.student_count = _student_count(section.id, db)
        return existing

    teacher_class = TeacherClass(
        teacher_id=teacher_id,
        class_name=f"{section.grade_level.name if section.grade_level else 'Grade'} - {section.name}",
        subject="Science",
        grade_level_id=section.grade_level_id,
        section_id=section.id,
        student_count=_student_count(section.id, db),
    )
    db.add(teacher_class)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return _teacher_class_for_section(section, teacher_id, db)
    db.refresh(teacher_class)
    result = (
        db.query(TeacherClass)
        .options(joinedload(TeacherClass.grade_levels), joinedload(TeacherClass.sections))
        .filter(TeacherClass.id == teacher_class.id)
        .first()
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to load selected class")
    result.student_count = _student_count(section.id, db)
    return result


@router.get("/available")
@limiter.limit("20/minute")
def list_available_sections(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user),
):
    _ensure_teacher(current_user)
    sections = (
        db.query(HI_SECTIONS)
        .options(joinedload(HI_SECTIONS.grade_level))
        .join(HI_SECTIONS.grade_level)
        .filter(GradeLevels.name.in_(ALLOWED_GRADE_NAMES))
        .order_by(HI_SECTIONS.grade_level_id.asc(), HI_SECTIONS.name.asc())
        .all()
    )
    return [_section_payload(section, current_user.id, db) for section in sections]


@router.post("/{section_id}/select", response_model=TeacherClassOut)
@limiter.limit("10/minute")
def select_section(
    request: Request,
    section_id: int,
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user),
):
    _ensure_teacher(current_user)
    section = (
        db.query(HI_SECTIONS)
        .options(joinedload(HI_SECTIONS.grade_level))
        .filter(HI_SECTIONS.id == section_id)
        .first()
    )
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
    get_grade_level_or_404(section.grade_level_id, db)
    if section.teacher_id and section.teacher_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Section is already assigned to another teacher")

    section.teacher_id = current_user.id
    db.commit()
    db.refresh(section)
    return _teacher_class_for_section(section, current_user.id, db)


@router.post("/{section_id}/unselect")
@limiter.limit("10/minute")
def unselect_section(
    request: Request,
    section_id: int,
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user),
):
    _ensure_teacher(current_user)
    section = (
        db.query(HI_SECTIONS)
        .options(joinedload(HI_SECTIONS.grade_level))
        .filter(HI_SECTIONS.id == section_id, HI_SECTIONS.teacher_id == current_user.id)
        .first()
    )
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found or not assigned to you")
    get_grade_level_or_404(section.grade_level_id, db)

    section.teacher_id = None
    db.commit()
    db.refresh(section)
    return _section_payload(section, current_user.id, db)
