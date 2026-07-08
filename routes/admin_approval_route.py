from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models.accounts import Accounts
from utils.dependencies import get_current_user, get_db
from services.admin_approval_service import admin_approval, teachers_pending_account

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.patch("/teachers/{teacher_id}/approve")
def admin_approval_routes(teacher_id: int, current_user: Accounts = Depends(get_current_user), db: Session = Depends(get_db)):
    return admin_approval(teacher_id=teacher_id, current_user=current_user, db=db)

@router.get("/teachers/pendings")
def teachers_pending_account_routes(current_user: Accounts = Depends(get_current_user), db: Session = Depends(get_db)):
    return teachers_pending_account(current_user=current_user, db=db)