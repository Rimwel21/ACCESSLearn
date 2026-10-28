from pydantic import BaseModel, EmailStr, Field, field_validator
from utils.enum import RoleEnum
from utils.password_policy import validate_new_password


class PasswordResetConfirmBase(BaseModel):
    new_password: str = Field(min_length=8, max_length=72)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value: str):
        return validate_new_password(value)


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

class TeacherPasswordResetConfirm(PasswordResetConfirmBase):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)
    role: RoleEnum = RoleEnum.teacher

class StudentPasswordResetRequest(BaseModel):
    username: str = Field(min_length=5, max_length=50)
    role: RoleEnum = RoleEnum.student

class StudentPasswordResetVerify(BaseModel):
    username: str = Field(min_length=5, max_length=50)
    otp: str = Field(min_length=6, max_length=6)
    role: RoleEnum = RoleEnum.student

class StudentPasswordResetConfirm(PasswordResetConfirmBase):
    username: str = Field(min_length=5, max_length=50)
    otp: str = Field(min_length=6, max_length=6)
    role: RoleEnum = RoleEnum.student

class AdminPasswordResetRequest(BaseModel):
    email: EmailStr
    role: RoleEnum = RoleEnum.admin

class AdminPasswordResetVerify(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)
    role: RoleEnum = RoleEnum.admin

class AdminPasswordResetConfirm(PasswordResetConfirmBase):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)
    role: RoleEnum = RoleEnum.admin
