from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.orm import Session

from limiter import limiter
from models.accounts import Accounts
from schemas.remediation_schema import RemediationActivityCreate, RemediationActivityOut, RemediationSubmit
from services.remediation_service import (
    create_remediation_activity,
    get_student_remediation_target,
    list_student_remediation_activities,
    list_teacher_remediation_activities,
    submit_student_remediation_target,
    upload_remediation_question_video,
)
from utils.dependencies import get_current_user, get_db


teacher_router = APIRouter(prefix="/teacher/remediation-activities", tags=["Targeted Support Activities"])
student_router = APIRouter(prefix="/student/remediation-activities", tags=["Targeted Support Activities"])


@teacher_router.get("/", response_model=list[RemediationActivityOut])
@limiter.limit("20/minute")
def list_teacher_remediation_route(request: Request, db: Session = Depends(get_db), current_user: Accounts = Depends(get_current_user)):
    return list_teacher_remediation_activities(db, current_user)


@teacher_router.post("/", response_model=RemediationActivityOut)
@limiter.limit("10/minute")
def create_teacher_remediation_route(
    request: Request,
    payload: RemediationActivityCreate,
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user),
):
    return create_remediation_activity(payload, db, current_user)


@teacher_router.post("/{activity_id}/interventions/{intervention_id}/questions/{question_index}/video", response_model=RemediationActivityOut)
@limiter.limit("10/minute")
async def upload_remediation_question_video_route(
    request: Request,
    activity_id: int,
    intervention_id: int,
    question_index: int,
    video: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user),
):
    return upload_remediation_question_video(activity_id, intervention_id, question_index, video, db, current_user)


@student_router.get("/")
@limiter.limit("20/minute")
def list_student_remediation_route(request: Request, db: Session = Depends(get_db), current_user: Accounts = Depends(get_current_user)):
    return list_student_remediation_activities(db, current_user)


@student_router.get("/{target_id}")
@limiter.limit("20/minute")
def get_student_remediation_route(target_id: int, request: Request, db: Session = Depends(get_db), current_user: Accounts = Depends(get_current_user)):
    return get_student_remediation_target(target_id, db, current_user)


@student_router.post("/{target_id}/submit")
@limiter.limit("20/minute")
def submit_student_remediation_route(
    target_id: int,
    payload: RemediationSubmit,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user),
):
    return submit_student_remediation_target(target_id, payload.answers, db, current_user)
