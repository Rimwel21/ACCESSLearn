from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from datetime import datetime
from utils.enum import RoleEnum


class AccountRegister(BaseModel):
    username: str | None = Field(None, min_length=5, max_length=50)
    email: EmailStr | None = None
    password: str = Field(min_length=8, max_length=30)
    role: RoleEnum
    
    # Optional Student Registration Fields
    fullName: str | None = None
    contactNo: str | None = None
    studentId: str | None = None
    grade_level_id: int | None = None
    section_id: int | None = None

    @model_validator(mode="before")
    @classmethod
    def sanitize_inputs(cls, data):
        if not isinstance(data, dict):
            return data
        
        fields = [
            "username",
            "email",
            "password"
        ]

        for field in fields:
            value = data.get(field)

            if isinstance(value, str):
                data[field] = value.strip()

        return data
    
    @model_validator(mode="after")
    def validate_password(self):

        if self.username and self.password.lower() == self.username.lower():
            raise ValueError("password must not be the same as username")
        
        return self

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str | None):
        if value is not None:
            if not value[0].isupper():
                raise ValueError("Invalid format. Use one uppercase at the beginning.")
        return value

class PublicGradeLevelOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class PublicSectionOut(BaseModel):
    id: int
    name: str
    grade_level_id: int
    subject: str | None = None
    school_year: str | None = None
    teacher_name: str | None = None

    class Config:
        from_attributes = True

    

class AccountLogin(BaseModel):
    username: str | None = Field(None, min_length=5, max_length=50)
    email: EmailStr | None = Field(None, min_length=5, max_length=50)
    password: str = Field(min_length=8, max_length=30)

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
    