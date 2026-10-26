from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint

from database.connection import Base
from utils.utc_now import utc_now


class StudentModuleLearningSummary(Base):
    """Ensures the teacher is notified once when a student finishes every checkpoint."""

    __tablename__ = "student_module_learning_summaries"
    __table_args__ = (
        UniqueConstraint("student_id", "module_id", name="uq_student_module_learning_summary"),
    )

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    module_id = Column(Integer, ForeignKey("teacher_modules.id", ondelete="CASCADE"), nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    teacher_notified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
