from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from schemas.teacher_assessment_schema import TeacherAssessmentOut
from utils.options import ALLOWED_LEARNING_WEEKS, ALLOWED_MODULE_CONTENT_TYPES


class TeacherModuleBase(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1)
    content_type: str | None = Field(default=None, max_length=60)
    week: str | None = Field(default=None, max_length=30)
    file_name: str | None = Field(default=None, max_length=255)
    file_type: str | None = Field(default=None, max_length=120)
    file_size: int | None = None
    status: str = Field(default="Unpublished", pattern="^(Published|Unpublished)$")
    behavior_required: bool = True
    class_id: int | None = None
    due_at: datetime | None = None


class TeacherModuleCreate(TeacherModuleBase):
    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, value: str | None):
        if value is not None and value not in ALLOWED_MODULE_CONTENT_TYPES:
            raise ValueError(f"Content type must be one of: {', '.join(ALLOWED_MODULE_CONTENT_TYPES)}")
        return value

    @field_validator("week")
    @classmethod
    def validate_week(cls, value: str | None):
        if value is not None and value not in ALLOWED_LEARNING_WEEKS:
            raise ValueError(f"Week must be one of: {', '.join(ALLOWED_LEARNING_WEEKS)}")
        return value


class TeacherModuleUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, min_length=1)
    content_type: str | None = Field(default=None, max_length=60)
    week: str | None = Field(default=None, max_length=30)
    file_name: str | None = Field(default=None, max_length=255)
    file_type: str | None = Field(default=None, max_length=120)
    file_size: int | None = None
    status: str | None = Field(default=None, pattern="^(Published|Unpublished)$")
    behavior_required: bool | None = None
    class_id: int | None = None
    due_at: datetime | None = None

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, value: str | None):
        if value is not None and value not in ALLOWED_MODULE_CONTENT_TYPES:
            raise ValueError(f"Content type must be one of: {', '.join(ALLOWED_MODULE_CONTENT_TYPES)}")
        return value

    @field_validator("week")
    @classmethod
    def validate_week(cls, value: str | None):
        if value is not None and value not in ALLOWED_LEARNING_WEEKS:
            raise ValueError(f"Week must be one of: {', '.join(ALLOWED_LEARNING_WEEKS)}")
        return value


class TeacherModuleOut(TeacherModuleBase):
    id: int
    teacher_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LearningTopicOut(BaseModel):
    id: int
    module_id: int
    title: str
    description: str | None = None
    content: str
    image_url: str | None = None
    page_image_urls: list[str] = []
    sort_order: int

    class Config:
        from_attributes = True


class TeacherModuleDetailOut(TeacherModuleOut):
    topics: list[LearningTopicOut] = []
    assessments: list[TeacherAssessmentOut] = []


class StudentProgressOut(BaseModel):
    completed_topic_ids: list[int]
    completed_quiz_ids: list[int] = []
    total_topics: int
    completed_topics: int
    total_quizzes: int = 0
    completed_quizzes: int = 0
    percent: int


class StudentDeadlineOut(BaseModel):
    id: str
    title: str
    item_type: str
    due_at: datetime
    module_id: int | None = None
    assessment_id: int | None = None
