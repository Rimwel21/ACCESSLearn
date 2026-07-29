from datetime import timedelta
from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session

from models.accounts import Accounts
from models.email_otp import EmailOTP
from utils.enum import RoleEnum, VerificationStatus
from utils.utc_now import utc_now
from core.teacher_email_otp import EmailService
from utils.generate_otp import hash_otp, generate_otp
from auth.account_auth import hash_password

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
        db.delete(pending_otp)
        db.commit()

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

    try:
        await EmailService.send_teacher_otp_email(email=email, otp=otp)
    except Exception as e:
        import sys
        print(f"\n=======================================================", file=sys.stderr)
        print(f"[REGISTRATION OTP] COULD NOT SEND EMAIL: {e}", file=sys.stderr)
        print(f"=======================================================\n", file=sys.stderr)
        db.delete(otp_record)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not send OTP email. Check the configured mail account and try again.",
        ) from e

    return {
        "message": "OTP sent successfully",
        "delivery": "sent",
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

async def request_teacher_password_reset_otp(request: Request, db: Session, email: str):
    account = db.query(Accounts).filter(
        Accounts.email == email,
        Accounts.role == RoleEnum.teacher,
    ).first()

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher account not found")

    if account.verification_status == VerificationStatus.blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Blocked account cannot reset password")

    expired_otps = db.query(EmailOTP).filter(
        EmailOTP.email == email,
        EmailOTP.role == RoleEnum.teacher,
        EmailOTP.expired_at < utc_now(),
        EmailOTP.verification_status == VerificationStatus.pending,
    ).all()

    for otp_record in expired_otps:
        db.delete(otp_record)

    pending_otp = db.query(EmailOTP).filter(
        EmailOTP.email == email,
        EmailOTP.role == RoleEnum.teacher,
        EmailOTP.verification_status == VerificationStatus.pending,
        EmailOTP.expired_at >= utc_now(),
    ).order_by(EmailOTP.created_at.desc()).first()

    if pending_otp:
        db.delete(pending_otp)

    otp = generate_otp()
    otp_record = EmailOTP(
        email=email,
        otp_hash=hash_otp(otp),
        role=RoleEnum.teacher,
        expired_at=utc_now() + timedelta(minutes=5),
        is_used=False,
        attempt_count=0,
        verification_status=VerificationStatus.pending,
    )

    db.add(otp_record)
    db.commit()

    try:
        await EmailService.send_teacher_otp_email(email=email, otp=otp)
    except Exception as e:
        import sys
        print(f"\n=======================================================", file=sys.stderr)
        print(f"[PASSWORD RESET OTP] COULD NOT SEND EMAIL: {e}", file=sys.stderr)
        print(f"=======================================================\n", file=sys.stderr)
        db.delete(otp_record)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not send OTP email. Check the configured mail account and try again.",
        ) from e

    return {
        "message": "OTP sent successfully",
        "delivery": "sent",
    }


def verify_teacher_password_reset_otp(db: Session, email: str, otp: str):
    otp_record = _get_password_reset_otp(db, email, otp)
    otp_record.attempt_count += 0
    db.commit()
    return {"message": "OTP verified. Enter a new password."}


def confirm_teacher_password_reset(db: Session, email: str, otp: str, new_password: str):
    account = db.query(Accounts).filter(
        Accounts.email == email,
        Accounts.role == RoleEnum.teacher,
    ).first()

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher account not found")

    _get_password_reset_otp(db, email, otp)
    otp_record = db.query(EmailOTP).filter(
        EmailOTP.email == email,
        EmailOTP.role == RoleEnum.teacher,
        EmailOTP.verification_status == VerificationStatus.pending,
        EmailOTP.is_used == False,
    ).order_by(EmailOTP.created_at.desc()).first()

    account.hashed_password = hash_password(new_password)
    otp_record.is_used = True
    otp_record.verification_status = VerificationStatus.verified
    db.commit()

    return {"message": "Password reset successfully. You can now log in."}


def _get_password_reset_otp(db: Session, email: str, otp: str):
    account = db.query(Accounts).filter(
        Accounts.email == email,
        Accounts.role == RoleEnum.teacher,
    ).first()

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher account not found")

    otp_record = db.query(EmailOTP).filter(
        EmailOTP.email == email,
        EmailOTP.role == RoleEnum.teacher,
        EmailOTP.verification_status == VerificationStatus.pending,
        EmailOTP.is_used == False,
    ).order_by(EmailOTP.created_at.desc()).first()

    if not otp_record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP not found")

    if otp_record.expired_at < utc_now():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP is expired!")

    if otp_record.otp_hash != hash_otp(otp):
        otp_record.attempt_count += 1
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")

    return otp_record


async def request_admin_password_reset_otp(request: Request, db: Session, email: str):
    account = db.query(Accounts).filter(
        Accounts.email == email,
        Accounts.role == RoleEnum.admin,
    ).first()

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin account not found")

    if account.verification_status == VerificationStatus.blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Blocked account cannot reset password")

    expired_otps = db.query(EmailOTP).filter(
        EmailOTP.email == email,
        EmailOTP.role == RoleEnum.admin,
        EmailOTP.expired_at < utc_now(),
        EmailOTP.verification_status == VerificationStatus.pending,
    ).all()

    for otp_record in expired_otps:
        db.delete(otp_record)

    pending_otp = db.query(EmailOTP).filter(
        EmailOTP.email == email,
        EmailOTP.role == RoleEnum.admin,
        EmailOTP.verification_status == VerificationStatus.pending,
        EmailOTP.expired_at >= utc_now(),
    ).order_by(EmailOTP.created_at.desc()).first()

    if pending_otp:
        db.delete(pending_otp)

    otp = generate_otp()
    otp_record = EmailOTP(
        email=email,
        otp_hash=hash_otp(otp),
        role=RoleEnum.admin,
        expired_at=utc_now() + timedelta(minutes=5),
        is_used=False,
        attempt_count=0,
        verification_status=VerificationStatus.pending,
    )

    db.add(otp_record)
    db.commit()

    try:
        await EmailService.send_admin_password_reset_otp_email(email=email, otp=otp)
    except Exception as exc:
        db.delete(otp_record)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not send OTP email. Check the configured mail account and try again.",
        ) from exc

    return {"message": "OTP sent to the admin email."}


def verify_admin_password_reset_otp(db: Session, email: str, otp: str):
    _get_role_password_reset_otp(db, email, otp, RoleEnum.admin)
    return {"message": "OTP verified. Enter a new password."}


def confirm_admin_password_reset(db: Session, email: str, otp: str, new_password: str):
    account = db.query(Accounts).filter(
        Accounts.email == email,
        Accounts.role == RoleEnum.admin,
    ).first()

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin account not found")

    otp_record = _get_role_password_reset_otp(db, email, otp, RoleEnum.admin)

    account.hashed_password = hash_password(new_password)
    otp_record.is_used = True
    otp_record.verification_status = VerificationStatus.verified
    db.commit()

    return {"message": "Password reset successfully. You can now log in."}


def _get_role_password_reset_otp(db: Session, email: str, otp: str, role: RoleEnum):
    account = db.query(Accounts).filter(
        Accounts.email == email,
        Accounts.role == role,
    ).first()

    if not account:
        detail = "Admin account not found" if role == RoleEnum.admin else "Teacher account not found"
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

    otp_record = db.query(EmailOTP).filter(
        EmailOTP.email == email,
        EmailOTP.role == role,
        EmailOTP.verification_status == VerificationStatus.pending,
        EmailOTP.is_used == False,
    ).order_by(EmailOTP.created_at.desc()).first()

    if not otp_record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP not found")

    if otp_record.expired_at < utc_now():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP is expired!")

    if otp_record.otp_hash != hash_otp(otp):
        otp_record.attempt_count += 1
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")

    return otp_record
