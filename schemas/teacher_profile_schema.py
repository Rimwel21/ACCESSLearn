from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from datetime import datetime
from utils.enum import GradeLevel, UserSex

class TeacherProfileBase(BaseModel):
    name: str = Field(min_length=5, max_length=50)
    age: int = Field(ge=18, le=100)
    sex: UserSex
    contact_no: str
    grade_level_handles: list[GradeLevel]
    address: str = Field(min_length=5, max_length=150)

    @model_validator(mode="before")
    @classmethod
    def sanitize_inputs(cls, data):
        if not isinstance(data, dict):
            return data

        for field in ["name", "contact_no", "address"]:
            value = data.get(field)
            if isinstance(value, str):
                data[field] = value.strip()

        return data

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str):
        if not value:
            raise ValueError("name cannot be empty")
        if not value[0].isupper():
            raise ValueError("First letter must be capitalized")
        return value

    @field_validator("contact_no")
    @classmethod
    def validate_contact_no(cls, value: str):
        if not value:
            raise ValueError("please include contact no.")
        if not value.startswith("0"):
            raise ValueError("Contact number must start with 0.")
        if not value.isdigit():
            raise ValueError("Contact number must contain only numbers.")
        if len(value) != 11:
            raise ValueError("Contact number consists of 11 numbers.")
        return value

    @field_validator("grade_level_handles")
    @classmethod
    def validate_grade_level_handles(cls, value: list[GradeLevel]):
        if not value:
            raise ValueError("include grade level handles")
        return value

class TeacherProfileCreate(TeacherProfileBase):
    pass

class TeacherProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=5, max_length=50)
    age: int | None = Field(default=None, ge=18, le=100)
    sex: UserSex | None = None
    contact_no: str | None = None
    grade_level_handles: list[GradeLevel] | None = None
    address: str | None = Field(default=None, min_length=5, max_length=150)

    @model_validator(mode="before")
    @classmethod
    def sanitize_inputs(cls, data):
        if not isinstance(data, dict):
            return data

        for field in ["name", "contact_no", "address"]:
            value = data.get(field)
            if isinstance(value, str):
                data[field] = value.strip()

        return data

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None):
        if value is not None and not value[0].isupper():
            raise ValueError("First letter must be capitalized")
        return value

    @field_validator("contact_no")
    @classmethod
    def validate_contact_no(cls, value: str | None):
        if value is None:
            return value
        if not value.startswith("0"):
            raise ValueError("Contact number must start with 0.")
        if not value.isdigit():
            raise ValueError("Contact number must contain only numbers.")
        if len(value) != 11:
            raise ValueError("Contact number consists of 11 numbers.")
        return value

    @field_validator("grade_level_handles")
    @classmethod
    def validate_grade_level_handles(cls, value: list[GradeLevel] | None):
        if value is not None and not value:
            raise ValueError("include grade level handles")
        return value


class TeacherGradeHandlesOut(BaseModel):
    grade_level_handles: GradeLevel

    class Config:
        from_attributes = True

class TeacherProfileOut(BaseModel):
    id: int
    account_id: int
    profile_image_id: int | None = None
    name: str
    age: int | None = None
    sex: UserSex | None = None
    handle_grade_levels: list[TeacherGradeHandlesOut] = []
    contact_no: str
    email_address: EmailStr
    address: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
