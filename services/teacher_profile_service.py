from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session
from utils.enum import RoleEnum
from models.accounts import Accounts
from models.teacher_profile import TeacherProfile
from schemas.teacher_profile_schema import TeacherProfileCreate, TeacherProfileUpdate

# get teacher profile
def get_teacher_profile(request: Request, db: Session, current_user: Accounts):
    if current_user.role != RoleEnum.teacher:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher only")
    
    teacher_profile = db.query(TeacherProfile).filter(TeacherProfile.account_id == current_user.id).first()

    if not teacher_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher profile not found")
    
    return teacher_profile

def create_teacher_profile(request: Request, teacher: TeacherProfileCreate, db: Session, current_user: Accounts):
    if current_user.role != RoleEnum.teacher:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher only")
    
    existing_profile = db.query(TeacherProfile).filter(TeacherProfile.account_id == current_user.id).first()

    if existing_profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Teacher profile already exists")
    
    new_teacher_profile = TeacherProfile(
        account_id=current_user.id,
        name=teacher.name,
        contact_no=teacher.contact_no,
        email_address=current_user.email,
        address=teacher.address,
    )

    db.add(new_teacher_profile)
    db.commit()
    db.refresh(new_teacher_profile)

    return new_teacher_profile

def update_teacher_profile(request: Request, update: TeacherProfileUpdate, db: Session, current_user: Accounts):
    if current_user.role != RoleEnum.teacher:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher only")
    
    teacher_profile = db.query(TeacherProfile).filter(TeacherProfile.account_id == current_user.id).first()

    if not teacher_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher profile not found")
    
    update_profile = update.model_dump(exclude_unset=True)

    for key, value in update_profile.items():
        setattr(teacher_profile, key, value)
    
    db.commit()
    db.refresh(teacher_profile)

    return teacher_profile