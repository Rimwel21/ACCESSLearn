from fastapi import Request, HTTPException, status, Response
from sqlalchemy.orm import Session
from utils.enum import RoleEnum, VerificationStatus, AccountStatusEnum
from models.accounts import Accounts
from schemas.accounts_schema import AccountRegister, AccountLogin
from models.student_profile import StudentProfile
from models.teacher_profile import TeacherProfile
from auth.account_auth import hash_password, verify_password, create_access_token, create_refresh_token

from models.email_otp import EmailOTP
from utils.utc_now import utc_now

def user_registration(request: Request, user: AccountRegister, db: Session):
    if user.role == RoleEnum.student:
        if not user.username:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username is required for student accounts")
        
        existing = db.query(Accounts).filter(Accounts.username == user.username).first()
        
    elif user.role == RoleEnum.teacher:
        if not user.email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is required for teacher accounts")
        
        verified_email = (
            db.query(EmailOTP).filter(EmailOTP.email == user.email, EmailOTP.role == RoleEnum.teacher, EmailOTP.verification_status == VerificationStatus.verified, EmailOTP.is_used == True).order_by(EmailOTP.created_at.desc()).first()
        )

        if not verified_email:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account must be verified by OTP before registration")
        
        existing = db.query(Accounts).filter(Accounts.email == user.email).first()

    elif user.role == RoleEnum.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin registration is not allowed")
    
    
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account already exists")
    
    new_account = Accounts(
        username=user.username if user.role == RoleEnum.student else None,
        email=user.email if user.role == RoleEnum.teacher else None,
        hashed_password=hash_password(user.password),
        role=user.role,
        verification_status=VerificationStatus.pending if user.role == RoleEnum.teacher else VerificationStatus.verified,
        account_status=AccountStatusEnum.pending_activation if user.role == RoleEnum.teacher else AccountStatusEnum.active
    )

    db.add(new_account)
    db.commit()
    db.refresh(new_account)

    return new_account

def user_login(request: Request, user: AccountLogin, response: Response, db: Session):
    if not user.username and not user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email is required"
        )
    
    if user.username and user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use only username or email"
        )

    if user.username:
        db_account = db.query(Accounts).filter(Accounts.username == user.username).first()
    else:
        db_account = db.query(Accounts).filter(Accounts.email == user.email).first()

    if not db_account:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    if db_account.verification_status == VerificationStatus.pending:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Wait for admin approval")
    
    if db_account.verification_status == VerificationStatus.blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You've been blocked from the system")

    if not verify_password(user.password, db_account.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access_token = create_access_token(
        data={
            "sub": str(db_account.id),
            "username": db_account.username,
            "email": db_account.email,
            "role": db_account.role
        }
    )

    refresh_token = create_refresh_token(
        data={
            "sub": str(db_account.id)
        }
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # True kapag HTTPS na
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        path="/api/refresh"
    )
    
    profile_completed = False

    # Student check if profile exists
    if db_account.role == RoleEnum.student:
        profile = db.query(StudentProfile).filter(StudentProfile.account_id == db_account.id).first()

        # chinecheck nito si user na nag lologin kung meron nabang profile
        profile_completed = profile is not None

    # check teacher profile if exists
    if db_account.role == RoleEnum.teacher:
        profile = db.query(TeacherProfile).filter(TeacherProfile.account_id == db_account.id).first()

        profile_completed = profile is not None
        
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "profile_completed": profile_completed
    }
