from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from schemas.teacher_assessment_schema import AssessmentQuestion


class RemediationQuestion(AssessmentQuestion):
    """A follow-up question, optionally presented through a teacher sign video."""

    source_question_index: int | None = Field(default=None, ge=0)
    prompt_type: Literal["text", "sign_video"] = "text"
    sign_video_url: str | None = None


class RemediationInterventionCreate(BaseModel):
    checkpoint_id: int | None = None
    start_sort_order: int = Field(ge=1)
    end_sort_order: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=160)
    instructions: str | None = Field(default=None, max_length=2000)
    questions: list[RemediationQuestion] = Field(min_length=1)
    student_ids: list[int] = Field(min_length=1)

    @field_validator("student_ids")
    @classmethod
    def distinct_students(cls, value: list[int]):
        return list(dict.fromkeys(value))


class RemediationActivityCreate(BaseModel):
    module_id: int
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=4000)
    due_at: datetime | None = None
    interventions: list[RemediationInterventionCreate] = Field(min_length=1)


class RemediationTargetOut(BaseModel):
    id: int
    student_id: int
    student_name: str | None = None
    status: str
    score: int | None = None
    total: int | None = None
    completed_at: datetime | None = None


class RemediationInterventionOut(BaseModel):
    id: int
    checkpoint_id: int | None = None
    start_sort_order: int
    end_sort_order: int
    title: str
    instructions: str | None = None
    questions: list[RemediationQuestion]
    video_url: str | None = None
    targets: list[RemediationTargetOut] = []


class RemediationActivityOut(BaseModel):
    id: int
    module_id: int
    title: str
    description: str
    due_at: datetime | None = None
    created_at: datetime
    interventions: list[RemediationInterventionOut]


class RemediationSubmit(BaseModel):
    answers: dict = Field(default_factory=dict)
