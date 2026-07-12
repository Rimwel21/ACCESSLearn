from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from database.connection import Base
from utils.utc_now import utc_now


class LearningTopic(Base):
    __tablename__ = "learning_topics"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    module_id = Column(Integer, ForeignKey("teacher_modules.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(160), nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    image_url = Column(String(500), nullable=True)
    page_image_urls = Column(JSON, default=list, nullable=False)
    sort_order = Column(Integer, default=1, nullable=False)

    module = relationship("TeacherModule", back_populates="topics")
    progress_records = relationship("StudentTopicProgress", back_populates="topic", cascade="all, delete-orphan", passive_deletes=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
