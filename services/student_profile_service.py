from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session
from utils.enum import RoleEnum
from models.accounts import Accounts
from models.student_profile import StudentProfile
from models.file_upload import FileUpload
from schemas.student_profile_schema import StudentProfileCreate, StudentProfileUpdate


def create_student_profile(request: Request, student: StudentProfileCreate, db: Session, current_user: Accounts):
    if current_user.role != RoleEnum.student:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student only")
    
    existing_profile = db.query(StudentProfile).filter(StudentProfile.account_id == current_user.id).first()

    if existing_profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student profile already exists")

    new_student_profile = StudentProfile(
        name=student.name,
        age=student.age,
        sex=student.sex,
        grade_level=student.grade_level,
        section=_normalize_section(student.section),
        account_id=current_user.id,
        profile_image_id=None,
        student_type=student.student_type,
        guardians_name=student.guardians_name,
        guardians_contact_no=student.guardians_contact_no,
        address=student.address   
    )

    db.add(new_student_profile)
    db.commit()
    db.refresh(new_student_profile)

    return new_student_profile

def update_student_profile(request: Request,update: StudentProfileUpdate, db: Session, current_user: Accounts):
    if current_user.role != RoleEnum.student:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student only")
    
    student_profile = db.query(StudentProfile).filter(StudentProfile.account_id == current_user.id).first()
    if not student_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")
    
    update_profile = update.model_dump(exclude_unset=True)

    for key, value in update_profile.items():
        if key == "section" and isinstance(value, str):
            value = _normalize_section(value)
        setattr(student_profile, key, value)

    db.commit()
    db.refresh(student_profile)

    return student_profile


def _normalize_section(section: str):
    return " ".join(section.strip().split()).upper()
    
def get_student_profile(request: Request, db: Session, current_user: Accounts):
    if current_user.role != RoleEnum.student:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student only")
    
    student_profile = db.query(StudentProfile).filter(StudentProfile.account_id == current_user.id).first()

    if not student_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

    return student_profile

