from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from models.accounts import Accounts
from services.admin_create_section_service import create_section
from schemas.create_section_schema import SectionCreate, SectionOut
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