from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from utils.options import ALLOWED_CLASS_SUBJECTS


class TeacherClassBase(BaseModel):
    class_name: str = Field(min_length=1, max_length=120)
    subject: str = Field(min_length=1, max_length=120)
    grade_level: str = Field(min_length=1, max_length=30)
    section: str = Field(min_length=1, max_length=50)
    school_year: str | None = Field(default=None, max_length=30)


class TeacherClassCreate(TeacherClassBase):
    @field_validator("subject")
    @classmethod
    def validate_subject(cls, value: str):
        if value not in ALLOWED_CLASS_SUBJECTS:
            raise ValueError(f"Subject must be one of: {', '.join(ALLOWED_CLASS_SUBJECTS)}")
        return value


class TeacherClassUpdate(BaseModel):
    class_name: str | None = Field(default=None, min_length=1, max_length=120)
    subject: str | None = Field(default=None, min_length=1, max_length=120)
    grade_level: str | None = Field(default=None, min_length=1, max_length=30)
    section: str | None = Field(default=None, min_length=1, max_length=50)
    school_year: str | None = Field(default=None, max_length=30)

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, value: str | None):
        if value is not None and value not in ALLOWED_CLASS_SUBJECTS:
            raise ValueError(f"Subject must be one of: {', '.join(ALLOWED_CLASS_SUBJECTS)}")
        return value


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


class DashboardStudentProgressOut(BaseModel):
    student_id: int
    student_name: str
    overall_percent: int
    activities_completed: int
    activities_total: int
    status: str
    last_activity: datetime | None = None
    quiz_activity: str | None = None


class RecentActivityOut(BaseModel):
    id: str
    text: str
    occurred_at: datetime
    activity_type: str


class TeacherDashboardSummaryOut(BaseModel):
    total_students: int
    active_learning_materials: int
    average_quiz_score: int
    student_progress: list[DashboardStudentProgressOut] = []
