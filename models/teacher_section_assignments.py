from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from database.connection import Base
from utils.utc_now import utc_now

class TeacherSectionAssignment(Base):
    __tablename__ = "teacher_section_assignments"

    id = Column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    teacher_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    section_id = Column(Integer, ForeignKey("hi_sections.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    teacher = relationship("Accounts", foreign_keys=[teacher_id])
    section = relationship("HI_SECTIONS", foreign_keys=[section_id])

    __table_args__ = (
        UniqueConstraint("teacher_id", "section_id", name="uq_teacher_section_assignment"),
    )
