from pydantic import BaseModel
from utils.enum import StudentType, GradeLevel, UserSex
from datetime import datetime

class StudentProfileBase(BaseModel):
    name: str
    age: int
    sex: UserSex
    grade_level: GradeLevel
    section: str
    student_type: StudentType
    guardians_name: str | None = None
    guardians_contact_no: str | None = None
    address: str | None = None

class StudentProfileCreate(StudentProfileBase):
    pass

class StudentProfileUpdate(BaseModel):
    name: str | None = None
    age: int | None = None
    sex: UserSex | None = None
    grade_level: GradeLevel | None = None
    section: str | None = None
    student_type: StudentType | None = None
    guardians_name: str | None = None
    guardians_contact_no: str | None = None
    address: str | None = None

class StudentProfileOut(BaseModel):
    id: int
    name: str
    age: int
    sex: UserSex
    grade_level: GradeLevel
    section: str
    student_type: StudentType
    account_id: int
    profile_image_id: int | None = None
    guardians_name: str | None = None
    guardians_contact_no: str | None = None
    address: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True