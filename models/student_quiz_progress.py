from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from database.connection import Base
from utils.utc_now import utc_now


class StudentQuizProgress(Base):
    __tablename__ = "student_quiz_progress"
    __table_args__ = (
        UniqueConstraint("student_id", "assessment_id", name="uq_student_quiz_progress"),
    )

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    module_id = Column(Integer, ForeignKey("teacher_modules.id", ondelete="CASCADE"), nullable=True, index=True)
    assessment_id = Column(Integer, ForeignKey("teacher_assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), default="in_progress", nullable=False)
    score = Column(Integer, nullable=True)
    total = Column(Integer, nullable=True)
    answers = Column(JSON, default=dict, nullable=False)

    started_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
