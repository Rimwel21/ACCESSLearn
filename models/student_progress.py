from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from database.connection import Base
from utils.utc_now import utc_now


class StudentTopicProgress(Base):
    __tablename__ = "student_topic_progress"
    __table_args__ = (
        UniqueConstraint("student_id", "topic_id", name="uq_student_topic_progress"),
    )

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    module_id = Column(Integer, ForeignKey("teacher_modules.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("learning_topics.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), default="in_progress", nullable=False)

    topic = relationship("LearningTopic", back_populates="progress_records")

    started_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
