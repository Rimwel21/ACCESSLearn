from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, UniqueConstraint
from database.connection import Base
from utils.utc_now import utc_now


class HandsignTutorialPractice(Base):
    __tablename__ = "handsign_tutorial_practice"
    __table_args__ = (
        UniqueConstraint("student_id", "activity_id", "canonical_word", name="uq_handsign_tutorial_practice"),
    )

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_id = Column(Integer, ForeignKey("teacher_assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    progress_id = Column(Integer, ForeignKey("student_quiz_progress.id", ondelete="SET NULL"), nullable=True, index=True)
    canonical_word = Column(String(80), nullable=False, index=True)
    attempt_scores = Column(JSON, default=list, nullable=False)
    highest_score = Column(Float, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
