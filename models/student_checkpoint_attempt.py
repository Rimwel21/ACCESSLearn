from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, UniqueConstraint
from sqlalchemy.orm import relationship

from database.connection import Base
from utils.utc_now import utc_now


class StudentCheckpointAttempt(Base):
    __tablename__ = "student_checkpoint_attempts"
    __table_args__ = (
        UniqueConstraint("student_id", "checkpoint_id", name="uq_student_checkpoint_attempt"),
    )

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    checkpoint_id = Column(Integer, ForeignKey("module_checkpoints.id", ondelete="CASCADE"), nullable=False, index=True)
    answers = Column(JSON, default=dict, nullable=False)
    score = Column(Integer, nullable=False, default=0)
    total = Column(Integer, nullable=False, default=0)
    completed_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    checkpoint = relationship("ModuleCheckpoint", back_populates="attempts")
