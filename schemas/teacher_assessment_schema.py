from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import re


class AssessmentQuestion(BaseModel):
    prompt: str = Field(min_length=1)
    answer: str | None = None
    question_type: str = Field(default="identification", pattern="^(identification|multiple_choice|true_false)$")
    options: list[str] = Field(default_factory=list, max_length=4)

    @field_validator("options")
    @classmethod
    def validate_options(cls, value: list[str]):
        return [option.strip() for option in value if option.strip()]


class TeacherAssessmentBase(BaseModel):
    class_id: int | None = None
    module_id: int | None = None
    topic_id: int | None = None
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1)
    category: str | None = Field(default=None, max_length=80)
    week: str | None = Field(default=None, max_length=30)
    time_limit: str | None = Field(default=None, max_length=30)
    time_limit_seconds: int | None = Field(default=None, ge=1)
    attempts_allowed: int = Field(default=1, ge=1, le=99)
    shuffle_questions: bool = True
    show_answers_after_submission: bool = True
    allow_text_answers: bool = False
    questions: list[AssessmentQuestion] = Field(default_factory=list)
    due_at: datetime | None = None


class TeacherAssessmentCreate(TeacherAssessmentBase):
    assessment_type: str = Field(pattern="^(quiz|activity)$")

    @field_validator("week")
    @classmethod
    def validate_week(cls, value: str | None):
        if value is not None and not re.fullmatch(r"Week ([1-9]|[1-9][0-9]{1,2})", value):
            raise ValueError("Week must be between Week 1 and Week 999.")
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
    time_limit_seconds: int | None = Field(default=None, ge=1)
    attempts_allowed: int | None = Field(default=None, ge=1, le=99)
    shuffle_questions: bool | None = None
    show_answers_after_submission: bool | None = None
    allow_text_answers: bool | None = None
    questions: list[AssessmentQuestion] | None = None
    due_at: datetime | None = None

    @field_validator("week")
    @classmethod
    def validate_week(cls, value: str | None):
        if value is not None and not re.fullmatch(r"Week ([1-9]|[1-9][0-9]{1,2})", value):
            raise ValueError("Week must be between Week 1 and Week 999.")
        return value


class TeacherActivityWeekCreate(BaseModel):
    week: str = Field(min_length=1, max_length=30)

    @field_validator("week")
    @classmethod
    def validate_week(cls, value: str):
        if not re.fullmatch(r"Week ([1-9]|[1-9][0-9]{1,2})", value):
            raise ValueError("Week must be between Week 1 and Week 999.")
        return value


class ActivitySubmissionOut(BaseModel):
    id: int
    student_id: int
    student_name: str
    score: int | None = None
    total: int | None = None
    answers: dict = Field(default_factory=dict)
    completed_at: datetime | None = None
    submission_type: str | None = None


class TeacherAssessmentOut(TeacherAssessmentBase):
    id: int
    teacher_id: int
    assessment_type: str
    student_status: str | None = None
    student_score: int | None = None
    student_total: int | None = None
    student_completed_at: datetime | None = None
    student_started_at: datetime | None = None
    student_expires_at: datetime | None = None
    student_remaining_seconds: int | None = None
    student_submission_type: str | None = None
    student_answers: dict = Field(default_factory=dict)
    student_answered_count: int = 0
    student_progress_percent: int = 0
    student_progress_status: str = "not_started"
    student_last_saved_at: datetime | None = None
    student_retake_eligible: bool = False
    student_retake_reason: str | None = None
    student_retake_status: str | None = None
    submissions_count: int = 0
    submissions: list[ActivitySubmissionOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ActivityDraftOut(BaseModel):
    activity_id: int
    status: str
    answered_count: int
    total_questions: int
    progress_percent: int
    last_saved_at: datetime
    submitted: bool = False


class ActivityProgressStudentOut(BaseModel):
    student_id: int
    student_name: str
    status: str
    answered_count: int
    unanswered_count: int
    total_questions: int
    progress_percent: int
    last_saved_at: datetime | None = None
    submitted: bool
    submitted_at: datetime | None = None
    is_currently_working: bool = False
    answers: dict = Field(default_factory=dict)


class ActivityProgressSummaryOut(BaseModel):
    total_students: int
    not_started: int
    in_progress: int
    draft_complete: int
    submitted: int
    missing: int
    late: int
    graded: int = 0
    started: int
    started_percent: int
    submitted_percent: int


class ActivityProgressOut(BaseModel):
    activity_id: int
    activity_title: str
    class_id: int
    class_name: str
    grade_level: str | None = None
    section: str | None = None
    due_at: datetime | None = None
    summary: ActivityProgressSummaryOut
    students: list[ActivityProgressStudentOut] = Field(default_factory=list)
