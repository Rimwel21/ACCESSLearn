from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from schemas.teacher_assessment_schema import AssessmentQuestion, TeacherAssessmentOut
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
    sign_videos: list["TopicSignVideoOut"] = []

    class Config:
        from_attributes = True


class TopicSignVideoOut(BaseModel):
    id: int
    learning_topic_id: int
    focus_area: str
    title: str
    video_url: str

    class Config:
        from_attributes = True


class ModuleCheckpointCreate(BaseModel):
    start_sort_order: int = Field(ge=1)
    end_sort_order: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=160)
    questions: list[AssessmentQuestion] = Field(min_length=5, max_length=5)


class ModuleCheckpointOut(ModuleCheckpointCreate):
    id: int
    student_status: str | None = None
    student_score: int | None = None
    student_total: int | None = None
    student_completed_at: datetime | None = None

    class Config:
        from_attributes = True


class TeacherModuleDetailOut(TeacherModuleOut):
    topics: list[LearningTopicOut] = []
    checkpoints: list[ModuleCheckpointOut] = []
    assessments: list[TeacherAssessmentOut] = []


class StudentProgressOut(BaseModel):
    completed_topic_ids: list[int]
    completed_quiz_ids: list[int] = []
    completed_checkpoint_ids: list[int] = []
    total_topics: int
    completed_topics: int
    total_quizzes: int = 0
    completed_quizzes: int = 0
    total_checkpoints: int = 0
    completed_checkpoints: int = 0
    percent: int


class StudentDeadlineOut(BaseModel):
    id: str
    title: str
    item_type: str
    due_at: datetime
    module_id: int | None = None
    assessment_id: int | None = None
