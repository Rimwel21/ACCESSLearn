from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database.connection import Base

class HI_SECTIONS(Base):
    __tablename__ = "hi_sections"

    id = Column(Integer, primary_key=True,unique=True, nullable=False, index=True)

    name = Column(String(100), nullable=False)

    grade_level_id = Column(Integer, ForeignKey("grade_levels.id", ondelete="CASCADE"), nullable=False, index=True)

    # relationship sa section
    grade_level = relationship("GradeLevels", back_populates="sections")

    # student profile relationship
    students = relationship("StudentProfile", back_populates="section")

    # teacher class relationship 
    teacher_classes = relationship("TeacherClass", back_populates="sections")
    