from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from database.connection import Base
from utils.utc_now import utc_now


class TeacherAssessment(Base):
    __tablename__ = "teacher_assessments"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("teacher_classes.id", ondelete="CASCADE"), nullable=True, index=True)
    module_id = Column(Integer, ForeignKey("teacher_modules.id", ondelete="CASCADE"), nullable=True, index=True)
    topic_id = Column(Integer, ForeignKey("learning_topics.id", ondelete="SET NULL"), nullable=True, index=True)
    assessment_type = Column(String(20), nullable=False, index=True)
    title = Column(String(120), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(80), nullable=True)
    week = Column(String(30), nullable=True)
    time_limit = Column(String(30), nullable=True)
    attempts_allowed = Column(Integer, default=1, nullable=False)
    shuffle_questions = Column(String(10), default="true", nullable=False)
    show_answers_after_submission = Column(String(10), default="true", nullable=False)
    questions = Column(JSON, default=list, nullable=False)

    teacher_account = relationship("Accounts", back_populates="teacher_assessments")
    teacher_class = relationship("TeacherClass")
    module = relationship("TeacherModule", back_populates="assessments")
    topic = relationship("LearningTopic")

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
