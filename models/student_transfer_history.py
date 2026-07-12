"""
StudentTransferHistory model.

Immutable record of every section/teacher transfer for a student.
Both from and to fields are nullable to handle edge cases (first assignment,
student without prior section, etc.).
"""
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, String
from database.connection import Base
from utils.utc_now import utc_now


class StudentTransferHistory(Base):
    __tablename__ = "student_transfer_history"

    id = Column(Integer, primary_key=True, index=True)

    student_account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)

    # Section transfer
    from_section_id = Column(Integer, ForeignKey("sections.id", ondelete="SET NULL"), nullable=True)
    to_section_id   = Column(Integer, ForeignKey("sections.id", ondelete="SET NULL"), nullable=True)

    # Teacher transfer
    from_teacher_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    to_teacher_id   = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)

    # Who performed the transfer
    transferred_by = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)

    reason     = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
