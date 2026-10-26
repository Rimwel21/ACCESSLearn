from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import relationship

from database.connection import Base
from utils.utc_now import utc_now


class RemediationTarget(Base):
    __tablename__ = "remediation_targets"
    __table_args__ = (
        UniqueConstraint("intervention_id", "student_id", name="uq_remediation_target"),
    )

    id = Column(Integer, primary_key=True, index=True)
    intervention_id = Column(Integer, ForeignKey("remediation_interventions.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="assigned")
    answers = Column(JSON, default=dict, nullable=False)
    score = Column(Integer, nullable=True)
    total = Column(Integer, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    intervention = relationship("RemediationIntervention", back_populates="targets")
