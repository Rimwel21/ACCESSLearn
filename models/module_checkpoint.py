from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import relationship

from database.connection import Base
from utils.utc_now import utc_now


class ModuleCheckpoint(Base):
    """A formative five-question check placed after a contiguous topic block."""

    __tablename__ = "module_checkpoints"
    __table_args__ = (
        UniqueConstraint("module_id", "start_sort_order", name="uq_module_checkpoint_start"),
    )

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("teacher_modules.id", ondelete="CASCADE"), nullable=False, index=True)
    start_sort_order = Column(Integer, nullable=False)
    end_sort_order = Column(Integer, nullable=False)
    title = Column(String(160), nullable=False)
    questions = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    module = relationship("TeacherModule", back_populates="checkpoints")
    attempts = relationship("StudentCheckpointAttempt", back_populates="checkpoint", cascade="all, delete-orphan", passive_deletes=True)
