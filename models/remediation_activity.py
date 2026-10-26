from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from database.connection import Base
from utils.utc_now import utc_now


class RemediationActivity(Base):
    """One teacher-posted support activity that can contain several student groups."""

    __tablename__ = "remediation_activities"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    module_id = Column(Integer, ForeignKey("teacher_modules.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    due_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    interventions = relationship("RemediationIntervention", back_populates="activity", cascade="all, delete-orphan", passive_deletes=True)
