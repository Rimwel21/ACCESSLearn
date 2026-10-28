from database.connection import SessionLocal
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError, ExpiredSignatureError
from core.config import settings
from models.accounts import Accounts
from services.audit_service import write_log
from utils.enum import AccountStatusEnum, AuditActionEnum, VerificationStatus
# db session
def get_db():

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# current user ng system
oauth2_scheme = HTTPBearer()

def get_current_user(request: Request, credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme), db: Session = Depends(get_db)):

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")
        
        user_id = int(user_id)
        
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
    user = db.query(Accounts).filter(Accounts.id == user_id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")

    allowed_account_statuses = {AccountStatusEnum.active, AccountStatusEnum.waiting_assignment}
    if user.verification_status != VerificationStatus.verified or user.account_status not in allowed_account_statuses:
        try:
            write_log(
                db,
                module="Authentication",
                action=AuditActionEnum.access_denied,
                actor_id=user.id,
                actor_role=user.role,
                affected_record=request.url.path,
                reason="Inactive, pending, suspended, archived, or blocked account used an existing token",
                request=request,
                status="failed",
            )
        except Exception:
            db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is not active")
    
    return user
