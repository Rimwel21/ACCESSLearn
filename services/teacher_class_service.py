from fastapi import HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from models.accounts import Accounts
from models.student_profile import StudentProfile
from models.teacher_class import TeacherClass
from schemas.teacher_class_schema import TeacherClassCreate, TeacherClassUpdate
from utils.enum import RoleEnum


def _ensure_teacher(current_user: Accounts):
    if current_user.role != RoleEnum.teacher:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher only")


def list_teacher_classes(request: Request, db: Session, current_user: Accounts):
    _ensure_teacher(current_user)

    classes = (
        db.query(TeacherClass)
        .filter(TeacherClass.teacher_id == current_user.id)
        .order_by(TeacherClass.created_at.desc())
        .all()
    )
    for teacher_class in classes:
        teacher_class.student_count = _count_matching_students(teacher_class, db)
    return classes


def create_teacher_class(request: Request, teacher_class: TeacherClassCreate, db: Session, current_user: Accounts):
    _ensure_teacher(current_user)

    new_teacher_class = TeacherClass(
        teacher_id=current_user.id,
        class_name=teacher_class.class_name.strip(),
        subject=teacher_class.subject.strip(),
        grade_level=_grade_value(teacher_class.grade_level),
        section=_normalize_section(teacher_class.section),
        school_year=teacher_class.school_year.strip() if teacher_class.school_year else None,
    )

    db.add(new_teacher_class)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Class already exists for this teacher, subject, grade level, and section"
        )

    db.refresh(new_teacher_class)
    new_teacher_class.student_count = _count_matching_students(new_teacher_class, db)

    return new_teacher_class


def get_teacher_class(request: Request, class_id: int, db: Session, current_user: Accounts):
    _ensure_teacher(current_user)

    teacher_class = (
        db.query(TeacherClass)
        .filter(TeacherClass.id == class_id, TeacherClass.teacher_id == current_user.id)
        .first()
    )

    if not teacher_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

    teacher_class.student_count = _count_matching_students(teacher_class, db)
    return teacher_class


def update_teacher_class(request: Request, class_id: int, update: TeacherClassUpdate, db: Session, current_user: Accounts):
    teacher_class = get_teacher_class(
        request=request,
        class_id=class_id,
        db=db,
        current_user=current_user
    )

    update_data = update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        if key == "grade_level" and value is not None:
            value = _grade_value(value)
        if key == "section" and isinstance(value, str):
            value = _normalize_section(value)
        setattr(teacher_class, key, value.strip() if isinstance(value, str) else value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Class already exists for this teacher, subject, grade level, and section"
        )

    db.refresh(teacher_class)
    teacher_class.student_count = _count_matching_students(teacher_class, db)

    return teacher_class


def delete_teacher_class(request: Request, class_id: int, db: Session, current_user: Accounts):
    teacher_class = get_teacher_class(
        request=request,
        class_id=class_id,
        db=db,
        current_user=current_user
    )

    db.delete(teacher_class)
    db.commit()

    return {"detail": "Class deleted successfully"}


def list_class_students(request: Request, class_id: int, db: Session, current_user: Accounts):
    teacher_class = get_teacher_class(
        request=request,
        class_id=class_id,
        db=db,
        current_user=current_user
    )

    return _matching_student_query(teacher_class, db).all()


def _matching_student_query(teacher_class: TeacherClass, db: Session):
    return (
        db.query(StudentProfile)
        .join(Accounts, Accounts.id == StudentProfile.account_id)
        .filter(
            StudentProfile.grade_level == teacher_class.grade_level,
            func.lower(func.trim(StudentProfile.section)) == _normalize_section(teacher_class.section).lower(),
            Accounts.role == RoleEnum.student,
        )
        .order_by(StudentProfile.name.asc())
    )


def _count_matching_students(teacher_class: TeacherClass, db: Session):
    return _matching_student_query(teacher_class, db).count()


def _grade_value(grade_level):
    return getattr(grade_level, "value", grade_level)


def _normalize_section(section: str):
    return " ".join(section.strip().split()).upper()
