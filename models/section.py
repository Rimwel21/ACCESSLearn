from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from database.connection import Base
from utils.enum import SectionStatusEnum
from utils.utc_now import utc_now

class Section(Base):
    __tablename__ = "sections"

    id           = Column(Integer, primary_key=True, index=True)
    name         = Column(String(100), nullable=False)             # e.g. "Sampaguita"
    capacity     = Column(Integer, default=40, nullable=False)
    subject      = Column(String(100), nullable=True)              # e.g. "Science"

    status = Column(
        Enum(SectionStatusEnum),
        default=SectionStatusEnum.active,
        nullable=False,
        index=True,
    )

    # Reference to central GradeLevel
    grade_level_id = Column(Integer, ForeignKey("grade_levels.id", ondelete="CASCADE"), nullable=False, index=True)
    grade_level    = relationship("GradeLevel", back_populates="sections")

    # Reference to central SchoolYear
    school_year_id = Column(Integer, ForeignKey("school_years.id", ondelete="SET NULL"), nullable=True, index=True)
    school_year    = relationship("SchoolYear")

    # Assigned teacher (one section → one teacher, nullable when unassigned)
    teacher_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    teacher    = relationship("Accounts", foreign_keys=[teacher_id])

    # Created by which admin
    created_by = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Students assigned to this section
    students = relationship("StudentProfile", back_populates="assigned_section")
