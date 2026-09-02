from datetime import datetime
from pydantic import BaseModel, Field


class TutorialStatus(BaseModel):
    word: str
    has_video: bool
    video_path: str | None
    video_url: str | None
    has_landmark_sample: bool
    landmark_sample_path: str | None
    has_practice_dataset: bool
    is_trained_in_word_model: bool
    reference_count: int
    can_practice: bool


class SequenceScoreRequest(BaseModel):
    word: str = Field(..., min_length=1)
    sequence: list[list[float]] = Field(..., min_length=1)


class FrameSequenceScoreRequest(BaseModel):
    word: str = Field(..., min_length=1)
    images: list[str] = Field(..., min_length=1)


class SequenceScoreResponse(BaseModel):
    target_word: str
    nearest_reference_index: int
    target_distance: float
    target_distance_threshold: float
    score: float


class PracticeResultCreate(BaseModel):
    activity_id: int
    word: str = Field(..., min_length=1)
    attempt_scores: list[float] = Field(..., min_length=3, max_length=3)


class PracticeResultOut(BaseModel):
    id: int
    activity_id: int
    student_id: int
    progress_id: int | None
    word: str
    attempt_scores: list[float]
    highest_score: float
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
