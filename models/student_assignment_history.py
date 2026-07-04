"""
StudentAssignmentHistory model.

Separate from transfer history — this records the original and subsequent
grade/section/teacher assignments, not just lateral transfers.

Sequence example:
  1. Admin assigns → Grade 5, Section A, Teacher X       (type = "assignment")
  2. Admin transfers → Grade 5, Section B, Teacher Y     (type = "transfer")
  3. Admin upgrades → Grade 6, Section A, Teacher Z      (type = "assignment")
"""
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, String, Enum
from database.connection import Base
from utils.utc_now import utc_now


class StudentAssignmentHistory(Base):
    __tablename__ = "student_assignment_history"

    id = Column(Integer, primary_key=True, index=True)

    student_account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)

    event_type = Column(String(20), default="assignment", nullable=False)  # assignment | transfer | upgrade

    section_id   = Column(Integer, ForeignKey("sections.id", ondelete="SET NULL"), nullable=True)
    teacher_id   = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    grade_level  = Column(String(20), nullable=True)

    assigned_by  = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    notes        = Column(Text, nullable=True)
    created_at   = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
