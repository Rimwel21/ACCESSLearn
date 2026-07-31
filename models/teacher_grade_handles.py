from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from database.connection import Base


class TeacherGradeHandles(Base):
    __tablename__ = "teacher_grade_handles"

    id = Column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    grade_level_id = Column(Integer, ForeignKey("grade_levels.id"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("teacher_profiles.id", ondelete="CASCADE"), nullable=False, index=True)

    teacher = relationship("TeacherProfile", back_populates="handle_grade_levels")
    grade_level = relationship("GradeLevels")
