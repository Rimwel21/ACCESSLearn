from fastapi import Request, HTTPException, status, Response
from sqlalchemy.orm import Session
from utils.enum import RoleEnum, VerificationStatus, AccountStatusEnum, StudentType
from models.accounts import Accounts
from schemas.accounts_schema import AccountRegister, AccountLogin
from models.student_profile import StudentProfile
from models.teacher_profile import TeacherProfile
from auth.account_auth import hash_password, verify_password, create_access_token, create_refresh_token
from services.academic_service import get_grade_level_or_404, get_section_for_grade_or_400

from models.email_otp import EmailOTP
from utils.utc_now import utc_now

def user_registration(request: Request, user: AccountRegister, db: Session):
    if user.role == RoleEnum.student:
        if not user.username:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username is required for student accounts")
        if not user.email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is required for student accounts")
        if not user.full_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Full name is required for student accounts")
        if not user.student_lrn:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student LRN is required")
        if user.grade_level_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Grade level is required")
        if user.section_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Section is required")
        if not user.accessibility_profile:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Accessibility profile is required")
        
        if db.query(Accounts).filter(Accounts.username == user.username).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
        if db.query(Accounts).filter(Accounts.email == user.email).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
        if db.query(StudentProfile).filter(StudentProfile.student_lrn == user.student_lrn).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student LRN already exists")

        get_grade_level_or_404(user.grade_level_id, db)
        get_section_for_grade_or_400(user.section_id, user.grade_level_id, db)
        existing = None
        
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
        email=user.email,
        hashed_password=hash_password(user.password),
        role=user.role,
        verification_status=VerificationStatus.pending if user.role == RoleEnum.teacher else VerificationStatus.verified,
        account_status=AccountStatusEnum.pending_activation if user.role == RoleEnum.teacher else AccountStatusEnum.active
    )

    db.add(new_account)
    db.flush()

    if user.role == RoleEnum.student:
        student_profile = StudentProfile(
            name=user.full_name,
            student_lrn=user.student_lrn,
            grade_level_id=user.grade_level_id,
            section_id=user.section_id,
            account_id=new_account.id,
            profile_image_id=None,
            student_type=StudentType.HI if user.accessibility_profile == "Hearing Impaired Student" else StudentType.regular,
            accessibility_profile=user.accessibility_profile,
            learning_preferences=None
        )
        db.add(student_profile)

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

    if user.email:
        query = db.query(Accounts).filter(Accounts.email == user.email)
        if user.role:
            query = query.filter(Accounts.role == user.role)
        db_account = query.first()

        if not db_account and user.role:
            other_account = db.query(Accounts).filter(Accounts.email == user.email).first()
            if other_account:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"This email belongs to a {other_account.role.value} account. Please use the {other_account.role.value} login.",
                )
    else:
        query = db.query(Accounts).filter(Accounts.username == user.username)
        if user.role:
            query = query.filter(Accounts.role == user.role)
        db_account = query.first()

    if not db_account:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    if db_account.verification_status == VerificationStatus.pending:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Wait for admin approval")

    if db_account.role == RoleEnum.teacher and db_account.account_status == AccountStatusEnum.pending_activation:
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
