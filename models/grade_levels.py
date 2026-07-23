from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
from database.connection import Base
from utils.enum import SectionStatusEnum
from utils.utc_now import utc_now

class GradeLevels(Base):
    __tablename__ = "grade_levels"

    id = Column(Integer, primary_key=True, unique=True, nullable=False, index=True)

    name = Column(String(20),unique=True, nullable=False)

    status = Column(Enum(SectionStatusEnum), default=SectionStatusEnum.active, nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # relationship sa section
    sections = relationship("HI_SECTIONS", back_populates="grade_level", passive_deletes=True)

    # relationship sa student
    students = relationship("StudentProfile", back_populates="grade_level")

    # relationship sa teacher class
    teacher_classes = relationship("TeacherClass", back_populates="grade_levels")
