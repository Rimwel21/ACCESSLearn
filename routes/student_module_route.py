from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from limiter import limiter
from models.accounts import Accounts
from schemas.teacher_module_schema import StudentProgressOut, TeacherModuleDetailOut
from schemas.teacher_assessment_schema import TeacherAssessmentOut
from services.student_module_service import (
    get_student_activity,
    get_module_progress,
    get_student_module,
    list_student_activities,
    list_student_modules,
    submit_assessment_progress,
    submit_class_activity_progress,
    submit_quiz_progress,
    update_topic_progress,
)
from utils.dependencies import get_current_user, get_db


class ProgressUpdate(BaseModel):
    status: str


class QuizSubmit(BaseModel):
    answers: dict = {}


router = APIRouter(prefix="/student/modules", tags=["Student Modules"])
activities_router = APIRouter(prefix="/student/activities", tags=["Student Activities"])


@activities_router.get("/", response_model=list[TeacherAssessmentOut])
@limiter.limit("20/minute")
def list_student_activities_route(request: Request, db: Session = Depends(get_db), current_user: Accounts = Depends(get_current_user)):
    return list_student_activities(request=request, db=db, current_user=current_user)


@activities_router.get("/{activity_id}", response_model=TeacherAssessmentOut)
@limiter.limit("20/minute")
def get_student_activity_route(request: Request, activity_id: int, db: Session = Depends(get_db), current_user: Accounts = Depends(get_current_user)):
    return get_student_activity(request=request, activity_id=activity_id, db=db, current_user=current_user)


@activities_router.post("/{activity_id}/submit")
@limiter.limit("20/minute")
def submit_student_activity_route(
    request: Request,
    activity_id: int,
    payload: QuizSubmit,
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user),
):
    return submit_class_activity_progress(
        request=request,
        activity_id=activity_id,
        answers=payload.answers,
        db=db,
        current_user=current_user,
    )


@router.get("/", response_model=list[TeacherModuleDetailOut])
@limiter.limit("20/minute")
def list_student_modules_route(request: Request, db: Session = Depends(get_db), current_user: Accounts = Depends(get_current_user)):
    return list_student_modules(request=request, db=db, current_user=current_user)


@router.get("/{module_id}", response_model=TeacherModuleDetailOut)
@limiter.limit("20/minute")
def get_student_module_route(request: Request, module_id: int, db: Session = Depends(get_db), current_user: Accounts = Depends(get_current_user)):
    return get_student_module(request=request, module_id=module_id, db=db, current_user=current_user)


@router.get("/{module_id}/progress", response_model=StudentProgressOut)
@limiter.limit("30/minute")
def get_module_progress_route(request: Request, module_id: int, db: Session = Depends(get_db), current_user: Accounts = Depends(get_current_user)):
    return get_module_progress(request=request, module_id=module_id, db=db, current_user=current_user)


@router.post("/{module_id}/topics/{topic_id}/progress", response_model=StudentProgressOut)
@limiter.limit("30/minute")
def update_topic_progress_route(
    request: Request,
    module_id: int,
    topic_id: int,
    payload: ProgressUpdate,
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user),
):
    return update_topic_progress(
        request=request,
        module_id=module_id,
        topic_id=topic_id,
        status_value=payload.status,
        db=db,
        current_user=current_user,
    )


@router.post("/{module_id}/quizzes/{quiz_id}/submit")
@limiter.limit("20/minute")
def submit_quiz_progress_route(
    request: Request,
    module_id: int,
    quiz_id: int,
    payload: QuizSubmit,
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user),
):
    return submit_quiz_progress(
        request=request,
        module_id=module_id,
        quiz_id=quiz_id,
        answers=payload.answers,
        db=db,
        current_user=current_user,
    )


@router.post("/{module_id}/assessments/{assessment_id}/submit")
@limiter.limit("20/minute")
def submit_assessment_progress_route(
    request: Request,
    module_id: int,
    assessment_id: int,
    payload: QuizSubmit,
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user),
):
    return submit_assessment_progress(
        request=request,
        module_id=module_id,
        assessment_id=assessment_id,
        answers=payload.answers,
        db=db,
        current_user=current_user,
    )
