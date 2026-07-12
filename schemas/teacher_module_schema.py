from datetime import datetime
from pydantic import BaseModel, Field
from schemas.teacher_assessment_schema import TeacherAssessmentOut


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
    estimated_time: str | None = Field(default=None, max_length=30)
    class_id: int | None = None


class TeacherModuleCreate(TeacherModuleBase):
    pass


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
    estimated_time: str | None = Field(default=None, max_length=30)
    class_id: int | None = None


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
