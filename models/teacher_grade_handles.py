from sqlalchemy import Column, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
from database.connection import Base
from utils.enum import GradeLevel


class TeacherGradeHandles(Base):
    __tablename__ = "teacher_grade_handles"

    id = Column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    grade_level_handles = Column(Enum(GradeLevel), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teacher_profiles.id", ondelete="CASCADE"), nullable=False, index=True)

    teacher = relationship("TeacherProfile", back_populates="handle_grade_levels")
