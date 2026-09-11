from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from database.connection import Base
from utils.utc_now import utc_now


class AssessmentRetakeRequest(Base):
    __tablename__ = "assessment_retake_requests"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_id = Column(Integer, ForeignKey("teacher_assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), default="pending", nullable=False, index=True)
    reason = Column(Text, nullable=True)
    request_type = Column(String(30), nullable=False)
    reviewed_by = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
