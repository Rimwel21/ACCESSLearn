from fastapi import  HTTPException, status
from sqlalchemy.orm import Session
from utils.enum import RoleEnum, VerificationStatus
from models.accounts import Accounts


def admin_approval(teacher_id: int, current_user: Accounts, db: Session):
    if current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    
    teacher = db.query(Accounts).filter(Accounts.id == teacher_id, Accounts.role == RoleEnum.teacher).first()

    if not teacher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher account not found")
    
    if teacher.verification_status == VerificationStatus.verified:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This teacher account has already been verified.")
    
    if teacher.verification_status == VerificationStatus.blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This teacher account has been blocked and cannot be approved.")

    if teacher.verification_status != VerificationStatus.pending:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This teacher account has already been processed.")


    teacher.verification_status = VerificationStatus.verified

    db.commit()
    db.refresh(teacher)

    return {"message": "teacher verified successfully!"}

def admin_block(teacher_id: int, current_user: Accounts, db: Session):
    if current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    
    teacher = db.query(Accounts).filter(Accounts.id == teacher_id, Accounts.role == RoleEnum.teacher).first()

    if not teacher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher account not found")
    
    if teacher.verification_status == VerificationStatus.blocked:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This teacher account has already been blocked.")

    teacher.verification_status = VerificationStatus.blocked

    db.commit()
    db.refresh(teacher)

    return {"message": "teacher blocked successfully!"}

def teachers_pending_account(current_user: Accounts, db: Session):
    if current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    
    teacher = (
        db.query(Accounts).filter(Accounts.role == RoleEnum.teacher, Accounts.verification_status == VerificationStatus.pending)
        .order_by(Accounts.created_at.desc())
        .all()
        )

    return teacher