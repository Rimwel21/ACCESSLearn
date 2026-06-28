from pydantic import BaseModel, EmailStr
from datetime import datetime
from utils.enum import UserSex, GradeLevel

class TeacherProfileBase(BaseModel):
    name: str
    contact_no: str
    age: int
    sex: UserSex

    # sa ibang table to mag sesave si grade_level_handles
    grade_level_handles: list[GradeLevel]
    address: str

class TeacherProfileCreate(TeacherProfileBase):
    pass

class TeacherProfileUpdate(BaseModel):
    name: str | None = None
    contact_no: str | None = None
    age: int | None = None
    sex: UserSex | None = None
    grade_level_handles: list[GradeLevel] | None = None
    address: str | None = None

# Table to ng GradeLevel, para sa teacher_grade_handles
class TeacherGradeHandlesOut(BaseModel):
    grade_level_handles: GradeLevel

    class Config:
        from_attributes = True

class TeacherProfileOut(BaseModel):
    id: int
    profile_image_id: int | None = None
    name: str
    age: int
    sex: UserSex

    # inherit
    handle_grade_levels: list[TeacherGradeHandlesOut]
    
    contact_no: str
    email_address: EmailStr
    address: str
    account_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True