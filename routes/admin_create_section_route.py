from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from models.accounts import Accounts
from services.admin_create_section_service import create_section, delete_section, update_section
from schemas.create_section_schema import SectionCreate, SectionOut, SectionUpdate
from utils.dependencies import get_db, get_current_user

router = APIRouter(prefix="/section", tags=["Section"])

@router.post("/create/admin", response_model=SectionOut)
def create_section_route(request: Request, section: SectionCreate, db: Session = Depends(get_db), current_user: Accounts = Depends(get_current_user)):
    return create_section(
        request=request,
        section=section,
        db=db,
        current_user=current_user
    )


@router.patch("/{section_id}", response_model=SectionOut)
def update_section_route(
    section_id: int,
    request: Request,
    section: SectionUpdate,
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user)
):
    return update_section(
        request=request,
        section_id=section_id,
        section=section,
        db=db,
        current_user=current_user
    )


@router.delete("/{section_id}")
def delete_section_route(
    section_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user)
):
    return delete_section(
        request=request,
        section_id=section_id,
        db=db,
        current_user=current_user
    )
