from pydantic import BaseModel, Field, EmailStr
from utils.enum import RoleEnum
class TeacherOtpRequest(BaseModel):
    email: EmailStr
    role: RoleEnum = RoleEnum.teacher

class TeacherOtpVerify(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)
    role: RoleEnum = RoleEnum.teacher