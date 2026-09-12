from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from limiter import limiter
from models.accounts import Accounts
from schemas.teacher_assessment_schema import TeacherAssessmentCreate, TeacherAssessmentOut, TeacherAssessmentUpdate
from services.teacher_assessment_service import (
    create_teacher_assessment,
    delete_teacher_assessment,
    list_retake_requests,
    list_teacher_assessments,
    review_retake_request,
    set_student_retake_access,
    update_teacher_assessment,
)
from utils.dependencies import get_current_user, get_db


router = APIRouter(prefix="/teacher/assessments", tags=["Teacher Assessments"])


class RetakeReviewBody(BaseModel):
    action: str


@router.get("/retake-requests")
@limiter.limit("20/minute")
def list_retake_requests_route(
    request: Request,
    status_filter: str | None = Query("pending", alias="status"),
    assessment_type: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user),
):
    return list_retake_requests(
        request=request,
        db=db,
        current_user=current_user,
        status_filter=status_filter,
        assessment_type=assessment_type,
    )


@router.patch("/retake-requests/{retake_id}")
@limiter.limit("20/minute")
def review_retake_request_route(
    request: Request,
    retake_id: int,
    body: RetakeReviewBody,
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user),
):
    return review_retake_request(
        request=request,
        retake_id=retake_id,
        action=body.action,
        db=db,
        current_user=current_user,
    )


@router.patch("/{assessment_id}/students/{student_id}/retake-access")
@limiter.limit("20/minute")
def set_student_retake_access_route(
    request: Request,
    assessment_id: int,
    student_id: int,
    body: RetakeReviewBody,
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user),
):
    return set_student_retake_access(
        request=request,
        assessment_id=assessment_id,
        student_id=student_id,
        action=body.action,
        db=db,
        current_user=current_user,
    )


@router.get("/{assessment_type}", response_model=list[TeacherAssessmentOut])
@limiter.limit("20/minute")
def list_teacher_assessments_route(request: Request, assessment_type: str, db: Session = Depends(get_db), current_user: Accounts = Depends(get_current_user)):
    return list_teacher_assessments(request=request, assessment_type=assessment_type, db=db, current_user=current_user)


@router.post("/", response_model=TeacherAssessmentOut)
@limiter.limit("10/minute")
def create_teacher_assessment_route(request: Request, assessment: TeacherAssessmentCreate, db: Session = Depends(get_db), current_user: Accounts = Depends(get_current_user)):
    return create_teacher_assessment(request=request, assessment=assessment, db=db, current_user=current_user)


@router.patch("/{assessment_id}", response_model=TeacherAssessmentOut)
@limiter.limit("10/minute")
def update_teacher_assessment_route(request: Request, assessment_id: int, update: TeacherAssessmentUpdate, db: Session = Depends(get_db), current_user: Accounts = Depends(get_current_user)):
    return update_teacher_assessment(request=request, assessment_id=assessment_id, update=update, db=db, current_user=current_user)


@router.delete("/{assessment_id}")
@limiter.limit("10/minute")
def delete_teacher_assessment_route(request: Request, assessment_id: int, db: Session = Depends(get_db), current_user: Accounts = Depends(get_current_user)):
    return delete_teacher_assessment(request=request, assessment_id=assessment_id, db=db, current_user=current_user)
