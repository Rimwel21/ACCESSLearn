from sqlalchemy import Column, Integer, ForeignKey, DateTime
from database.connection import Base
from utils.utc_now import utc_now

class TeacherAssignmentHistory(Base):
    __tablename__ = "teacher_assignment_history"

    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("sections.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_teacher_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    new_teacher_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_by = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
