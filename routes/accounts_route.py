from fastapi import APIRouter, Depends, Response, Request
from sqlalchemy.orm import Session
from utils.dependencies import get_current_user, get_db
from schemas.accounts_schema import AccountRegister, AccountLogin, AccountResponse, CurrentUserResponse, TokenResponse
from models.accounts import Accounts
from models.student_profile import StudentProfile
from models.teacher_profile import TeacherProfile
from utils.enum import RoleEnum
from limiter import limiter

from services.auth_service import user_registration, user_login

router = APIRouter(prefix="/auth", tags=["Auth"])

# Account Registration routes
@router.post("/account/register", response_model=AccountResponse)
@limiter.limit("5/minute")
def account_register(request:Request, user: AccountRegister, db: Session = Depends(get_db)):
    new_account = user_registration(
        request=request,
        user=user,
        db=db
    )

    return new_account

# Account Login routes
@router.post("/account/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def account_login(request:Request, user: AccountLogin, response: Response, db: Session = Depends(get_db)):
    Access_permission = user_login(
        request=request,
        user=user,
        response=response,
        db=db
    )

    return Access_permission

@router.get("/me", response_model=CurrentUserResponse)
@limiter.limit("20/minute")
def current_account(request: Request, current_user: Accounts = Depends(get_current_user), db: Session = Depends(get_db)):
    profile_completed = True

    if current_user.role == RoleEnum.student:
        profile_completed = db.query(StudentProfile.id).filter(StudentProfile.account_id == current_user.id).first() is not None
    elif current_user.role == RoleEnum.teacher:
        profile_completed = db.query(TeacherProfile.id).filter(TeacherProfile.account_id == current_user.id).first() is not None

    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "profile_completed": profile_completed,
        "account_status": enum_value(current_user.account_status),
    }

def enum_value(value):
    return getattr(value, "value", value)
