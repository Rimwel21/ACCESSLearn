from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload
from utils.enum import RoleEnum
from models.accounts import Accounts
from models.teacher_profile import TeacherProfile
from models.teacher_grade_handles import TeacherGradeHandles
from schemas.teacher_profile_schema import TeacherProfileCreate, TeacherProfileUpdate
from services.academic_service import get_grade_level_or_404

def create_teacher_profile(request: Request, teacher: TeacherProfileCreate, db: Session, current_user: Accounts):
    if current_user.role != RoleEnum.teacher:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher only")
    
    existing_profile = db.query(TeacherProfile).filter(TeacherProfile.account_id == current_user.id).first()

    if existing_profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Teacher profile already exists")
    
    new_teacher_profile = TeacherProfile(
        account_id=current_user.id,
        name=teacher.name,
        age=teacher.age,
        sex=teacher.sex,
        contact_no=teacher.contact_no,
        email_address=current_user.email,
        address=teacher.address,
    )

    db.add(new_teacher_profile)
    db.flush()

    for grade_level_id in teacher.grade_level_ids:
        get_grade_level_or_404(grade_level_id, db)
        db.add(TeacherGradeHandles(
            grade_level_id=grade_level_id,
            teacher_id=new_teacher_profile.id
        ))

    db.commit()

    return (
        db.query(TeacherProfile)
        .options(joinedload(TeacherProfile.handle_grade_levels).joinedload(TeacherGradeHandles.grade_level))
        .filter(TeacherProfile.id == new_teacher_profile.id)
        .first()
    )

def update_teacher_profile(request: Request, update: TeacherProfileUpdate, db: Session, current_user: Accounts):
    if current_user.role != RoleEnum.teacher:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher only")
    
    teacher_profile = db.query(TeacherProfile).filter(TeacherProfile.account_id == current_user.id).first()

    if not teacher_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher profile not found")
    
    update_profile = update.model_dump(exclude_unset=True, exclude={"grade_level_ids"})

    for key, value in update_profile.items():
        setattr(teacher_profile, key, value)

    if update.grade_level_ids is not None:
        db.query(TeacherGradeHandles).filter(
            TeacherGradeHandles.teacher_id == teacher_profile.id
        ).delete()

        for grade_level_id in update.grade_level_ids:
            get_grade_level_or_404(grade_level_id, db)
            db.add(TeacherGradeHandles(
                grade_level_id=grade_level_id,
                teacher_id=teacher_profile.id
            ))
    
    db.commit()

    return (
        db.query(TeacherProfile)
        .options(joinedload(TeacherProfile.handle_grade_levels).joinedload(TeacherGradeHandles.grade_level))
        .filter(TeacherProfile.id == teacher_profile.id)
        .first()
    )

def get_teacher_profile(request: Request, db: Session, current_user: Accounts):
    if current_user.role != RoleEnum.teacher:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher only")

    teacher_profile = (
        db.query(TeacherProfile)
        .options(joinedload(TeacherProfile.handle_grade_levels).joinedload(TeacherGradeHandles.grade_level))
        .filter(TeacherProfile.account_id == current_user.id)
        .first()
    )

    if not teacher_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher profile not found")

    return teacher_profile
