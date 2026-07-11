from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
from database.connection import Base
from utils.enum import SectionStatusEnum
from utils.utc_now import utc_now

class GradeLevel(Base):
    __tablename__ = "grade_levels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False) # e.g. "Grade 4"
    status = Column(Enum(SectionStatusEnum), default=SectionStatusEnum.active, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    sections = relationship("Section", back_populates="grade_level", cascade="all, delete-orphan")
