from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from database.connection import Base
from utils.utc_now import utc_now


class RemediationIntervention(Base):
    __tablename__ = "remediation_interventions"

    id = Column(Integer, primary_key=True, index=True)
    remediation_activity_id = Column(Integer, ForeignKey("remediation_activities.id", ondelete="CASCADE"), nullable=False, index=True)
    checkpoint_id = Column(Integer, ForeignKey("module_checkpoints.id", ondelete="SET NULL"), nullable=True, index=True)
    start_sort_order = Column(Integer, nullable=False)
    end_sort_order = Column(Integer, nullable=False)
    title = Column(String(160), nullable=False)
    instructions = Column(String(2000), nullable=True)
    questions = Column(JSON, default=list, nullable=False)
    video_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    activity = relationship("RemediationActivity", back_populates="interventions")
    targets = relationship("RemediationTarget", back_populates="intervention", cascade="all, delete-orphan", passive_deletes=True)
