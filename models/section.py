"""
Section model.

Tracks grade-level sections, assigned teacher, capacity, and lifecycle status.
Capacity logic (current_count, available_slots, percentage) is computed at
the service layer rather than stored — avoids denormalisation.
"""
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database.connection import Base
from utils.enum import SectionStatusEnum, GradeLevel
from utils.utc_now import utc_now


class Section(Base):
    __tablename__ = "sections"

    id           = Column(Integer, primary_key=True, index=True)
    name         = Column(String(100), nullable=False)             # e.g. "Sampaguita"
    grade_level  = Column(Enum(GradeLevel), nullable=False, index=True)
    capacity     = Column(Integer, default=40, nullable=False)

    status = Column(
        Enum(SectionStatusEnum),
        default=SectionStatusEnum.active,
        nullable=False,
        index=True,
    )

    # Assigned teacher (one section → one teacher, nullable when unassigned)
    teacher_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    teacher    = relationship("Accounts", foreign_keys=[teacher_id])

    # Created by which admin
    created_by = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
