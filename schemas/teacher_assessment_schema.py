from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from utils.options import ALLOWED_LEARNING_WEEKS


class AssessmentQuestion(BaseModel):
    prompt: str = Field(min_length=1)
    answer: str | None = None


class TeacherAssessmentBase(BaseModel):
    class_id: int | None = None
    module_id: int | None = None
    topic_id: int | None = None
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1)
    category: str | None = Field(default=None, max_length=80)
    week: str | None = Field(default=None, max_length=30)
    time_limit: str | None = Field(default=None, max_length=30)
    attempts_allowed: int = Field(default=1, ge=1, le=99)
    shuffle_questions: bool = True
    show_answers_after_submission: bool = True
    questions: list[AssessmentQuestion] = Field(default_factory=list)
    due_at: datetime | None = None


class TeacherAssessmentCreate(TeacherAssessmentBase):
    assessment_type: str = Field(pattern="^(quiz|activity)$")

    @field_validator("week")
    @classmethod
    def validate_week(cls, value: str | None):
        if value is not None and value not in ALLOWED_LEARNING_WEEKS:
            raise ValueError(f"Week must be one of: {', '.join(ALLOWED_LEARNING_WEEKS)}")
        return value


class TeacherAssessmentUpdate(BaseModel):
    class_id: int | None = None
    module_id: int | None = None
    topic_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, min_length=1)
    category: str | None = Field(default=None, max_length=80)
    week: str | None = Field(default=None, max_length=30)
    time_limit: str | None = Field(default=None, max_length=30)
    attempts_allowed: int | None = Field(default=None, ge=1, le=99)
    shuffle_questions: bool | None = None
    show_answers_after_submission: bool | None = None
    questions: list[AssessmentQuestion] | None = None
    due_at: datetime | None = None

    @field_validator("week")
    @classmethod
    def validate_week(cls, value: str | None):
        if value is not None and value not in ALLOWED_LEARNING_WEEKS:
            raise ValueError(f"Week must be one of: {', '.join(ALLOWED_LEARNING_WEEKS)}")
        return value


class ActivitySubmissionOut(BaseModel):
    id: int
    student_id: int
    student_name: str
    score: int | None = None
    total: int | None = None
    answers: dict = Field(default_factory=dict)
    completed_at: datetime | None = None


class TeacherAssessmentOut(TeacherAssessmentBase):
    id: int
    teacher_id: int
    assessment_type: str
    student_status: str | None = None
    student_score: int | None = None
    student_total: int | None = None
    student_completed_at: datetime | None = None
    submissions_count: int = 0
    submissions: list[ActivitySubmissionOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
