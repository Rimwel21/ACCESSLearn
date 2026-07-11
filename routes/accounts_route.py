from fastapi import APIRouter, Depends, Response, Request
from sqlalchemy.orm import Session
from utils.dependencies import get_db
from schemas.accounts_schema import AccountRegister, AccountLogin, AccountResponse, TokenResponse, PublicGradeLevelOut, PublicSectionOut
from limiter import limiter
from models.grade_level import GradeLevel
from models.section import Section
from models.student_profile import StudentProfile
from models.accounts import Accounts
from utils.enum import AccountStatusEnum
from typing import List

from services.auth_service import user_registration, user_login

router = APIRouter(prefix="/auth", tags=["Auth"])

# Public endpoints for student registration dropdowns (Active elements only)
@router.get("/grade-levels", response_model=List[PublicGradeLevelOut])
def get_public_grade_levels(db: Session = Depends(get_db)):
    return db.query(GradeLevel).filter(GradeLevel.status == "active").order_by(GradeLevel.name).all()

@router.get("/sections", response_model=List[PublicSectionOut])
def get_public_sections(grade_level_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Section).filter(Section.status == "active", Section.teacher_id != None)
    if grade_level_id:
        query = query.filter(Section.grade_level_id == grade_level_id)
    sections = query.all()
    
    result = []
    for sec in sections:
        # Check capacity based on active and pending student accounts
        student_count = db.query(StudentProfile).join(Accounts).filter(
            StudentProfile.section_id == sec.id,
            Accounts.account_status.in_([AccountStatusEnum.active, AccountStatusEnum.pending_approval])
        ).count()
        
        if student_count < sec.capacity:
            teacher_name = None
            if sec.teacher:
                profile = sec.teacher.teacher_profile
                if profile:
                    teacher_name = profile.name
                else:
                    teacher_name = sec.teacher.email or sec.teacher.username
            
            result.append(PublicSectionOut(
                id=sec.id,
                name=sec.name,
                grade_level_id=sec.grade_level_id,
                subject=sec.subject,
                school_year=sec.school_year.name if sec.school_year else None,
                teacher_name=teacher_name
            ))
            
    return result

# Account Registration routes
@router.post("/account/register", response_model=AccountResponse)
@limiter.limit("5/minute")
def account_register(request: Request, user: AccountRegister, db: Session = Depends(get_db)):
    new_account = user_registration(
        request=request,
        user=user,
        db=db
    )
    return new_account

# Account Login routes
@router.post("/account/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def account_login(request: Request, user: AccountLogin, response: Response, db: Session = Depends(get_db)):
    Access_permission = user_login(
        request=request,
        user=user,
        response=response,
        db=db
    )
    return Access_permission