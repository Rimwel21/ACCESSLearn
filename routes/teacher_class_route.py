from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from limiter import limiter
from models.accounts import Accounts
from schemas.teacher_class_schema import ClassStudentOut, TeacherClassCreate, TeacherClassOut, TeacherClassUpdate
from services.teacher_class_service import (
    create_teacher_class,
    delete_teacher_class,
    get_teacher_class,
    list_class_students,
    list_teacher_classes,
    update_teacher_class,
)
from utils.dependencies import get_current_user, get_db


router = APIRouter(prefix="/teacher/classes", tags=["Teacher Classes"])


@router.get("/", response_model=list[TeacherClassOut])
@limiter.limit("20/minute")
def list_teacher_classes_route(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user)
):
    return list_teacher_classes(
        request=request,
        db=db,
        current_user=current_user
    )


@router.post("/", response_model=TeacherClassOut)
@limiter.limit("10/minute")
def create_teacher_class_route(
    request: Request,
    teacher_class: TeacherClassCreate,
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user)
):
    return create_teacher_class(
        request=request,
        teacher_class=teacher_class,
        db=db,
        current_user=current_user
    )


@router.get("/{class_id}", response_model=TeacherClassOut)
@limiter.limit("20/minute")
def get_teacher_class_route(
    request: Request,
    class_id: int,
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user)
):
    return get_teacher_class(
        request=request,
        class_id=class_id,
        db=db,
        current_user=current_user
    )


@router.get("/{class_id}/students", response_model=list[ClassStudentOut])
@limiter.limit("20/minute")
def list_class_students_route(
    request: Request,
    class_id: int,
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user)
):
    return list_class_students(
        request=request,
        class_id=class_id,
        db=db,
        current_user=current_user
    )


@router.patch("/{class_id}", response_model=TeacherClassOut)
@limiter.limit("10/minute")
def update_teacher_class_route(
    request: Request,
    class_id: int,
    update: TeacherClassUpdate,
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user)
):
    return update_teacher_class(
        request=request,
        class_id=class_id,
        update=update,
        db=db,
        current_user=current_user
    )


@router.delete("/{class_id}")
@limiter.limit("10/minute")
def delete_teacher_class_route(
    request: Request,
    class_id: int,
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user)
):
    return delete_teacher_class(
        request=request,
        class_id=class_id,
        db=db,
        current_user=current_user
    )
