from datetime import timedelta
from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session

from models.accounts import Accounts
from models.email_otp import EmailOTP
from utils.enum import RoleEnum, VerificationStatus
from utils.utc_now import utc_now
from core.teacher_email_otp import EmailService
from utils.generate_otp import hash_otp, generate_otp

async def request_teacher_otp(request:Request,db: Session, email: str):
    existing_account = db.query(Accounts).filter(Accounts.email == email).first()

    pending_otp = (
        db.query(EmailOTP).filter(EmailOTP.email == email, EmailOTP.verification_status == VerificationStatus.pending, EmailOTP.expired_at >= utc_now()).order_by(EmailOTP.created_at.desc()).first()
    )
    
    expired_otps = db.query(EmailOTP).filter(EmailOTP.email == email, EmailOTP.expired_at < utc_now(), EmailOTP.verification_status == VerificationStatus.pending).all()

    if expired_otps:
        for otp in expired_otps:
            db.delete(otp)

        db.commit()

    if pending_otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please wait, there's still pending email, wait for otp expiration.") 

    if existing_account:
        if existing_account.verification_status == VerificationStatus.pending:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already created, and waiting for admins approval")

        if existing_account.verification_status == VerificationStatus.verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
        if existing_account.verification_status == VerificationStatus.blocked:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="blocked account cannot request otp")
    
    
    otp = generate_otp()

    otp_record = EmailOTP(
        email=email,
        otp_hash=hash_otp(otp),
        role=RoleEnum.teacher,
        expired_at=utc_now() + timedelta(minutes=5),
        is_used=False,
        attempt_count=0,
        verification_status=VerificationStatus.pending
    )

    db.add(otp_record)
    db.commit()
    db.refresh(otp_record)

    await EmailService.send_teacher_otp_email(email=email, otp=otp)

    return {
        "message": "OTP sent successfully"
    }

def verify_teacher_otp(db:Session, email:str, otp:str):
    otp_record = (db.query(EmailOTP).filter(EmailOTP.email == email, EmailOTP.role == RoleEnum.teacher,EmailOTP.verification_status == VerificationStatus.pending).order_by(EmailOTP.created_at.desc())
    .first()
    )

    existing_account = (
        db.query(Accounts).filter(Accounts.email == email).first()
    )
    
    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP not found"
        )

    if existing_account:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account already created")
    
    if otp_record.is_used:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="otp already used")
    
    if otp_record.expired_at < utc_now():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP is expired!")
    
    if otp_record.otp_hash != hash_otp(otp):
        otp_record.attempt_count += 1
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )
    
    otp_record.is_used = True
    otp_record.verification_status = VerificationStatus.verified

    db.commit()

    return {
        "message": "OTP verified successfully"
    }