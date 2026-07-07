from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from database.connection import Base
from utils.utc_now import utc_now


class TeacherModule(Base):
    __tablename__ = "teacher_modules"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("teacher_classes.id", ondelete="SET NULL"), nullable=True, index=True)

    title = Column(String(120), nullable=False)
    description = Column(Text, nullable=False)
    content_type = Column(String(60), nullable=True)
    week = Column(String(30), nullable=True)
    file_name = Column(String(255), nullable=True)
    file_type = Column(String(120), nullable=True)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    status = Column(String(20), default="Unpublished", nullable=False)
    behavior_required = Column(String(10), default="true", nullable=False)
    estimated_time = Column(String(30), nullable=True)

    teacher_account = relationship("Accounts", back_populates="teacher_modules")
    teacher_class = relationship("TeacherClass", back_populates="modules")
    topics = relationship("LearningTopic", back_populates="module", cascade="all, delete-orphan", passive_deletes=True)
    assessments = relationship("TeacherAssessment", back_populates="module", passive_deletes=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
