import re
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from datetime import datetime
from utils.enum import RoleEnum, VerificationStatus


class AccountRegister(BaseModel):
    username: str | None = Field(None, min_length=5, max_length=50)
    email: EmailStr | None = Field(None, min_length=5, max_length=50)
    password: str = Field(min_length=8, max_length=30)
    role: RoleEnum
    full_name: str | None = Field(None, min_length=2, max_length=100)
    student_lrn: str | None = Field(None, min_length=12, max_length=12)
    grade_level_id: int | None = None
    section_id: int | None = None
    accessibility_profile: str | None = None

    @model_validator(mode="before")
    @classmethod
    def sanitize_inputs(cls, data):
        if not isinstance(data, dict):
            return data

        for field in ["username", "email", "password", "full_name", "student_lrn", "accessibility_profile"]:
            value = data.get(field)
            if isinstance(value, str):
                data[field] = value.strip()

        return data

    @model_validator(mode="after")
    def validate_registration(self):
        if self.username and self.password.lower() == self.username.lower():
            raise ValueError("password must not be the same as username")
        
        if self.role == RoleEnum.student:
            if not self.username:
                raise ValueError("Username is required for student accounts")
            if not self.email:
                raise ValueError("Email is required for student accounts")
            if not self.full_name:
                raise ValueError("Full name is required for student accounts")
            if not self.student_lrn:
                raise ValueError("Student LRN is required")
            if self.grade_level_id is None:
                raise ValueError("Grade level is required")
            if self.section_id is None:
                raise ValueError("Section is required")
            if not self.accessibility_profile:
                raise ValueError("Accessibility profile is required")

            allowed_accessibility = {"Regular Student", "Hearing Impaired Student"}
            if self.accessibility_profile not in allowed_accessibility:
                raise ValueError("Accessibility profile must be Regular Student or Hearing Impaired Student")

        return self

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str | None):
        if value is None:
            return value

        if not value.replace("-", "").isalnum():
            raise ValueError("Invalid format. Use only letters, numbers, and hyphens.")

        return value

    @field_validator("student_lrn")
    @classmethod
    def validate_student_lrn(cls, value: str | None):
        if value is None:
            return value

        if not re.fullmatch(r"\d{12}", value):
            raise ValueError("Student LRN must be exactly 12 digits.")

        return value

class AccountLogin(BaseModel):
    username: str | None = Field(None, min_length=5, max_length=50)
    email: EmailStr | None = Field(None, min_length=5, max_length=50)
    password: str = Field(min_length=8, max_length=30)
    role: RoleEnum | None = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    profile_completed: bool

class AccountResponse(BaseModel):
    id: int
    username: str | None
    email: EmailStr | None
    role: RoleEnum
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PendingTeacherResponse(BaseModel):
    id: int
    email: EmailStr | None
    role: RoleEnum
    verification_status: VerificationStatus
    created_at: datetime

    class Config:
        from_attributes = True
    
