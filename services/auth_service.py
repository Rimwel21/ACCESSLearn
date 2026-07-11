from fastapi import Request, HTTPException, status, Response
from sqlalchemy.orm import Session
from utils.enum import RoleEnum, AccountStatusEnum, AuditActionEnum
from models.accounts import Accounts
from schemas.accounts_schema import AccountRegister, AccountLogin
from models.student_profile import StudentProfile
from models.teacher_profile import TeacherProfile
from models.grade_level import GradeLevel
from models.section import Section
from auth.account_auth import hash_password, verify_password, create_access_token, create_refresh_token
from services.audit_service import write_log

def user_registration(request: Request, user: AccountRegister, db: Session):
    if user.role == RoleEnum.student:
        if not user.username:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username is required for student accounts")
        if not user.grade_level_id or not user.section_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Grade level and Section are required")
        
        # Check active grade level
        grade = db.query(GradeLevel).filter(GradeLevel.id == user.grade_level_id, GradeLevel.status == "active").first()
        if not grade:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or archived grade level")
            
        section = db.query(Section).filter(Section.id == user.section_id, Section.status == "active").first()
        if not section:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or archived section")
        if section.grade_level_id != user.grade_level_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Grade level does not match section")
        if not section.teacher_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Section does not have an assigned teacher yet")
        
        # Check capacity: active and pending approval count
        active_and_pending_students = db.query(StudentProfile).join(Accounts).filter(
            StudentProfile.section_id == section.id,
            Accounts.account_status.in_([AccountStatusEnum.active, AccountStatusEnum.pending_approval])
        ).count()
        if active_and_pending_students >= section.capacity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Section is already full.")
            
        existing = db.query(Accounts).filter(Accounts.username == user.username).first()
        
    elif user.role == RoleEnum.teacher:
        if not user.email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is required for teacher accounts")

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
        account_status=AccountStatusEnum.pending_approval if user.role == RoleEnum.student else AccountStatusEnum.pending_activation
    )

    db.add(new_account)
    db.commit()
    db.refresh(new_account)

    if user.role == RoleEnum.student:
        # Create StudentProfile record immediately
        new_profile = StudentProfile(
            name=user.fullName if user.fullName else (user.username or ""),
            age=None, # Incomplete profile until ProfileSetup
            sex=None,
            student_type=None,
            grade_level_id=user.grade_level_id,
            section_id=user.section_id,
            account_id=new_account.id
        )
        db.add(new_profile)
        db.commit()
        
        write_log(
            db,
            module="StudentManagement",
            action=AuditActionEnum.created,
            actor_id=new_account.id,
            actor_role=new_account.role,
            affected_record=f"Student registration {new_profile.name}",
            request=request
        )

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

    # Pending approval students can log in to view setup/pending screen, but let's check
    # if we block them from logging in OR let them check status page.
    # In some systems they log in only when active. Let's allow them to log in to see setup profile if they haven't.
    # But if they are pending approval, verify if they are blocked from accessing other pages.
    # The requirement: "After registration, the student's account status becomes: Pending Approval."
    # Let's keep it simple: they can login, let's process their profile_completed flag.
    # If they are approved, they are active.

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
        secure=False,  # True in HTTPS
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        path="/api/refresh"
    )
    
    profile_completed = False

    # Student check if profile exists and has age set (completed profile setup step)
    if db_account.role == RoleEnum.student:
        profile = db.query(StudentProfile).filter(StudentProfile.account_id == db_account.id).first()
        profile_completed = profile is not None and profile.age is not None

    # Check teacher profile if exists
    if db_account.role == RoleEnum.teacher:
        profile = db.query(TeacherProfile).filter(TeacherProfile.account_id == db_account.id).first()
        profile_completed = profile is not None

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "profile_completed": profile_completed
    }
