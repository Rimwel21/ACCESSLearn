from datetime import datetime
from pydantic import BaseModel, Field


class TeacherClassBase(BaseModel):
    class_name: str = Field(min_length=1, max_length=120)
    subject: str = Field(min_length=1, max_length=120)
    grade_level: str = Field(min_length=1, max_length=30)
    section: str = Field(min_length=1, max_length=50)
    school_year: str | None = Field(default=None, max_length=30)


class TeacherClassCreate(TeacherClassBase):
    pass


class TeacherClassUpdate(BaseModel):
    class_name: str | None = Field(default=None, min_length=1, max_length=120)
    subject: str | None = Field(default=None, min_length=1, max_length=120)
    grade_level: str | None = Field(default=None, min_length=1, max_length=30)
    section: str | None = Field(default=None, min_length=1, max_length=50)
    school_year: str | None = Field(default=None, max_length=30)


class TeacherClassOut(TeacherClassBase):
    id: int
    teacher_id: int
    student_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ClassStudentOut(BaseModel):
    id: int
    account_id: int
    name: str
    username: str | None = None
    email: str | None = None
    grade_level: str | None = None
    section: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
