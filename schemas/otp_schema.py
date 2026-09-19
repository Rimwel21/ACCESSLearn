from pydantic import BaseModel, Field, EmailStr
from utils.enum import RoleEnum
class TeacherOtpRequest(BaseModel):
    email: EmailStr
    role: RoleEnum = RoleEnum.teacher

class TeacherOtpVerify(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)
    role: RoleEnum = RoleEnum.teacher

class TeacherPasswordResetRequest(BaseModel):
    email: EmailStr
    role: RoleEnum = RoleEnum.teacher

class TeacherPasswordResetVerify(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)
    role: RoleEnum = RoleEnum.teacher

class TeacherPasswordResetConfirm(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)
    new_password: str = Field(min_length=8, max_length=30)
    role: RoleEnum = RoleEnum.teacher

class StudentPasswordResetRequest(BaseModel):
    username: str = Field(min_length=5, max_length=50)
    role: RoleEnum = RoleEnum.student

class StudentPasswordResetVerify(BaseModel):
    username: str = Field(min_length=5, max_length=50)
    otp: str = Field(min_length=6, max_length=6)
    role: RoleEnum = RoleEnum.student

class StudentPasswordResetConfirm(BaseModel):
    username: str = Field(min_length=5, max_length=50)
    otp: str = Field(min_length=6, max_length=6)
    new_password: str = Field(min_length=8, max_length=30)
    role: RoleEnum = RoleEnum.student

class AdminPasswordResetRequest(BaseModel):
    email: EmailStr
    role: RoleEnum = RoleEnum.admin

class AdminPasswordResetVerify(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)
    role: RoleEnum = RoleEnum.admin

class AdminPasswordResetConfirm(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)
    new_password: str = Field(min_length=8, max_length=30)
    role: RoleEnum = RoleEnum.admin
