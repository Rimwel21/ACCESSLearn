from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from database.connection import Base
from utils.utc_now import utc_now


class TopicSignVideo(Base):
    """Teacher sign-language support attached to one extracted learning topic."""

    __tablename__ = "topic_sign_videos"
    __table_args__ = (
        UniqueConstraint("learning_topic_id", "focus_area", name="uq_topic_sign_video_focus"),
    )

    id = Column(Integer, primary_key=True, index=True)
    learning_topic_id = Column(Integer, ForeignKey("learning_topics.id", ondelete="CASCADE"), nullable=False, index=True)
    focus_area = Column(String(40), nullable=False)
    title = Column(String(160), nullable=False)
    video_url = Column(String(500), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    learning_topic = relationship("LearningTopic", back_populates="sign_videos")
