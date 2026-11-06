from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone
from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain:str, hashed: str)-> bool:
    return pwd_context.verify(plain, hashed)


# access token
def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire, "token_type": ACCESS_TOKEN_TYPE})

    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


# refresh token
def create_refresh_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_expire_days)

    to_encode.update({"exp": expire, "token_type": REFRESH_TOKEN_TYPE})

    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
