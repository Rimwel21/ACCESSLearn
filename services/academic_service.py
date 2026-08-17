from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.grade_levels import GradeLevels
from models.HI_sections import HI_SECTIONS
from utils.enum import SectionStatusEnum

ALLOWED_GRADE_NAMES = ("Grade 4", "Grade 5", "Grade 6")


def list_grade_levels(db: Session):
    grade_levels = (
        db.query(GradeLevels)
        .filter(GradeLevels.name.in_(ALLOWED_GRADE_NAMES))
        .order_by(GradeLevels.id.asc())
        .all()
    )

    if grade_levels:
        return grade_levels

    default_grade_levels = [
        GradeLevels(name=f"Grade {level}", status=SectionStatusEnum.active)
        for level in range(4, 7)
    ]
    db.add_all(default_grade_levels)
    db.commit()

    return (
        db.query(GradeLevels)
        .filter(GradeLevels.name.in_(ALLOWED_GRADE_NAMES))
        .order_by(GradeLevels.id.asc())
        .all()
    )


def list_sections(db: Session, grade_level_id: int | None = None):
    query = db.query(HI_SECTIONS).join(GradeLevels, HI_SECTIONS.grade_level_id == GradeLevels.id)

    if grade_level_id is not None:
        get_grade_level_or_404(grade_level_id, db)
        query = query.filter(HI_SECTIONS.grade_level_id == grade_level_id)
    else:
        query = query.filter(GradeLevels.name.in_(ALLOWED_GRADE_NAMES))

    return query.order_by(HI_SECTIONS.id.asc()).all()


def get_grade_level_or_404(grade_level_id: int, db: Session):
    grade_level = (
        db.query(GradeLevels)
        .filter(GradeLevels.id == grade_level_id)
        .filter(GradeLevels.name.in_(ALLOWED_GRADE_NAMES))
        .first()
    )

    if not grade_level:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grade level not found"
        )

    return grade_level


def get_section_for_grade_or_400(section_id: int, grade_level_id: int, db: Session):
    section = (
        db.query(HI_SECTIONS)
        .filter(
            HI_SECTIONS.id == section_id,
            HI_SECTIONS.grade_level_id == grade_level_id
        )
        .first()
    )

    if not section:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid section for selected grade level"
        )

    return section
