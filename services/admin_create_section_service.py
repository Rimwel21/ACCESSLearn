from fastapi import HTTPException, status, Depends, Request
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from models.accounts import Accounts
from models.HI_sections import HI_SECTIONS
from schemas.create_section_schema import SectionCreate
from utils.enum import RoleEnum
from services.academic_service import get_grade_level_or_404

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

    result = (
        db.query(HI_SECTIONS)
        .options(joinedload(HI_SECTIONS.grade_level))
        .filter(HI_SECTIONS.id == new_section.id)
        .first()
    )

    return result
