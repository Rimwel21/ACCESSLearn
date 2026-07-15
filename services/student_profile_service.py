from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload
from utils.enum import RoleEnum
from models.accounts import Accounts
from models.student_profile import StudentProfile
from services.academic_service import get_grade_level_or_404, get_section_for_grade_or_400
from schemas.student_profile_schema import StudentProfileCreate, StudentProfileUpdate

def student_current_user(current_user: Accounts):
    if current_user.role != RoleEnum.student:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student only")
def create_student_profile(request: Request, student: StudentProfileCreate, db: Session, current_user: Accounts):
    student_current_user(current_user)
    
    existing_profile = db.query(StudentProfile).filter(StudentProfile.account_id == current_user.id).first()

    if existing_profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student profile already exists")

    get_grade_level_or_404(student.grade_level_id, db)
    get_section_for_grade_or_400(student.section_id, student.grade_level_id, db)

    new_student_profile = StudentProfile(
        name=student.name,
        age=student.age,
        sex=student.sex,
        grade_level_id=student.grade_level_id,
        section_id=student.section_id,
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

    result = (
        db.query(StudentProfile)
        .options(
            joinedload(StudentProfile.grade_level), #dito pinapakita lahat ng object or row ng grade level table, since eto ay relationship, pero yung may id lang na same sa ginawang grade_level_id
            joinedload(StudentProfile.section) # ganon din dito, pinapakita ang object or row ng section table
        )
        .filter(StudentProfile.id == new_student_profile.id)
        .first()
    )
    return result

def update_student_profile(request: Request,update: StudentProfileUpdate, db: Session, current_user: Accounts):
    student_current_user(current_user)
    
    student_profile = db.query(StudentProfile).filter(StudentProfile.account_id == current_user.id).first()
    if not student_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")
    
    update_profile = update.model_dump(exclude_unset=True)
    grade_level_id = "grade_level_id"
    section_id = "section_id"

    selected_grade_level_id = update_profile.get(
        grade_level_id,
        student_profile.grade_level_id
    )
        

    for key, value in update_profile.items():
        
        if key == grade_level_id:
            get_grade_level_or_404(value, db)
            
        elif key == section_id:
            get_section_for_grade_or_400(value, selected_grade_level_id, db)
            
        setattr(student_profile, key, value)
    

    db.commit()
    db.refresh(student_profile)

    result = (
        db.query(StudentProfile)
        .options(
            joinedload(StudentProfile.grade_level),
            joinedload(StudentProfile.section)
        )
        .filter(StudentProfile.id == student_profile.id)
        .first()
    )

    return result
    
def get_student_profile(request: Request, db: Session, current_user: Accounts):
    student_current_user(current_user)
    
    student_profile = (
        db.query(StudentProfile)
        .options(
            joinedload(StudentProfile.grade_level),
            joinedload(StudentProfile.section)
        )
        .filter(StudentProfile.account_id == current_user.id)
        .first()
    )

    if not student_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

    return student_profile

