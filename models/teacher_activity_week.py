from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint

from database.connection import Base
from utils.utc_now import utc_now


class TeacherActivityWeek(Base):
    __tablename__ = "teacher_activity_weeks"
    __table_args__ = (UniqueConstraint("teacher_id", "week", name="uq_teacher_activity_week"),)

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    week = Column(String(30), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
