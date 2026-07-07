from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from limiter import limiter
from models.accounts import Accounts
from schemas.teacher_assessment_schema import TeacherAssessmentCreate, TeacherAssessmentOut, TeacherAssessmentUpdate
from services.teacher_assessment_service import create_teacher_assessment, delete_teacher_assessment, list_teacher_assessments, update_teacher_assessment
from utils.dependencies import get_current_user, get_db


router = APIRouter(prefix="/teacher/assessments", tags=["Teacher Assessments"])


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
