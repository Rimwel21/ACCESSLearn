from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from limiter import limiter
from models.accounts import Accounts
from schemas.academic_schema import GradeLevelOut, SectionOut
from services.academic_service import list_grade_levels, list_sections
from utils.dependencies import get_current_user, get_db


router = APIRouter(prefix="/academic", tags=["Academic Data"])


@router.get("/public/grade-levels", response_model=list[GradeLevelOut])
@limiter.limit("30/minute")
def list_public_grade_levels_route(
    request: Request,
    db: Session = Depends(get_db)
):
    return list_grade_levels(db)


@router.get("/public/sections", response_model=list[SectionOut])
@limiter.limit("30/minute")
def list_public_sections_route(
    request: Request,
    grade_level_id: int | None = Query(default=None),
    db: Session = Depends(get_db)
):
    return list_sections(db, grade_level_id)


@router.get("/grade-levels", response_model=list[GradeLevelOut])
@limiter.limit("30/minute")
def list_grade_levels_route(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user)
):
    return list_grade_levels(db)


@router.get("/sections", response_model=list[SectionOut])
@limiter.limit("30/minute")
def list_sections_route(
    request: Request,
    grade_level_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user)
):
    return list_sections(db, grade_level_id)
