from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from utils.dependencies import get_db
from schemas.otp_schema import TeacherOtpVerify, TeacherOtpRequest
from services.otp_service import verify_teacher_otp, request_teacher_otp
from limiter import limiter
router = APIRouter(
    prefix="/otp",
    tags=["OTP"]
)

@router.post("/teacher/request")
@limiter.limit("2/minute")
async def request_teacher_otp_route(request: Request,payload: TeacherOtpRequest, db: Session = Depends(get_db)):
    return await request_teacher_otp(request=request, db=db, email=payload.email)

@router.post("/teacher/verify")
async def verify_teacher_otp_route(payload: TeacherOtpVerify, db: Session = Depends(get_db)):
    return verify_teacher_otp(db=db,email=payload.email, otp=payload.otp)