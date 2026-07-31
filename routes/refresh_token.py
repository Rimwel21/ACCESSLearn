from fastapi import APIRouter, HTTPException, status, Depends, Request
from jose import jwt, JWTError, ExpiredSignatureError
from sqlalchemy.orm import Session
from utils.dependencies import get_db
from models.accounts import Accounts
from models.student_profile import StudentProfile
from models.teacher_profile import TeacherProfile
from schemas.accounts_schema import TokenResponse
from auth.account_auth import create_access_token
from core.config import settings
from utils.enum import RoleEnum

router = APIRouter(prefix="/api", tags=["RefreshToken"])

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("refresh_token")

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        user_id = int(user_id)

        user = db.query(Accounts).filter(Accounts.id == user_id).first()

        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")

        new_access_token = create_access_token(
            data={
                "sub": str(user_id),
                "username": user.username,
                "email": user.email,
                "role": user.role
            }            
        )

        profile_completed = True
        if user.role == RoleEnum.student:
            profile_completed = db.query(StudentProfile.id).filter(StudentProfile.account_id == user.id).first() is not None
        elif user.role == RoleEnum.teacher:
            profile_completed = db.query(TeacherProfile.id).filter(TeacherProfile.account_id == user.id).first() is not None

        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "profile_completed": profile_completed,
        }

    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
