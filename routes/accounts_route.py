from fastapi import APIRouter, Depends, Response, Request
from sqlalchemy.orm import Session
from utils.dependencies import get_db
from schemas.accounts_schema import AccountRegister, AccountLogin, AccountResponse,TokenResponse
from limiter import limiter

from services.auth_service import user_registration, user_login

router = APIRouter(prefix="/auth", tags=["Auth"])

# Account Registration routes
@router.post("/account/register", response_model=AccountResponse)
@limiter.limit("5/minute")
def account_register(request:Request, user: AccountRegister, db: Session = Depends(get_db)):
    new_account = user_registration(
        request=request,
        user=user,
        db=db
    )

    return new_account

# Account Login routes
@router.post("/account/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def account_login(request:Request, user: AccountLogin, response: Response, db: Session = Depends(get_db)):
    Access_permission = user_login(
        request=request,
        user=user,
        response=response,
        db=db
    )

    return Access_permission