from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from utils.dependencies import get_db
from schemas.otp_schema import (
    TeacherOtpVerify,
    TeacherOtpRequest,
    TeacherPasswordResetRequest,
    TeacherPasswordResetVerify,
    TeacherPasswordResetConfirm,
    AdminPasswordResetRequest,
    AdminPasswordResetVerify,
    AdminPasswordResetConfirm,
)
from services.otp_service import (
    verify_teacher_otp,
    request_teacher_otp,
    request_teacher_password_reset_otp,
    verify_teacher_password_reset_otp,
    confirm_teacher_password_reset,
    request_admin_password_reset_otp,
    verify_admin_password_reset_otp,
    confirm_admin_password_reset,
)
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

@router.post("/teacher/password-reset/request")
@limiter.limit("2/minute")
async def request_teacher_password_reset_route(request: Request, payload: TeacherPasswordResetRequest, db: Session = Depends(get_db)):
    return await request_teacher_password_reset_otp(request=request, db=db, email=payload.email)

@router.post("/teacher/password-reset/verify")
async def verify_teacher_password_reset_route(payload: TeacherPasswordResetVerify, db: Session = Depends(get_db)):
    return verify_teacher_password_reset_otp(db=db, email=payload.email, otp=payload.otp)

@router.post("/teacher/password-reset/confirm")
async def confirm_teacher_password_reset_route(payload: TeacherPasswordResetConfirm, db: Session = Depends(get_db)):
    return confirm_teacher_password_reset(db=db, email=payload.email, otp=payload.otp, new_password=payload.new_password)

@router.post("/admin/password-reset/request")
@limiter.limit("2/minute")
async def request_admin_password_reset_route(request: Request, payload: AdminPasswordResetRequest, db: Session = Depends(get_db)):
    return await request_admin_password_reset_otp(request=request, db=db, email=payload.email)

@router.post("/admin/password-reset/verify")
async def verify_admin_password_reset_route(payload: AdminPasswordResetVerify, db: Session = Depends(get_db)):
    return verify_admin_password_reset_otp(db=db, email=payload.email, otp=payload.otp)

@router.post("/admin/password-reset/confirm")
async def confirm_admin_password_reset_route(payload: AdminPasswordResetConfirm, db: Session = Depends(get_db)):
    return confirm_admin_password_reset(db=db, email=payload.email, otp=payload.otp, new_password=payload.new_password)
