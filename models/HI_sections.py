from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database.connection import Base


class HI_SECTIONS(Base):
    __tablename__ = "hi_sections"

    id = Column(Integer, primary_key=True, unique=True, nullable=False, index=True)

    name = Column(String(100), nullable=False)

    grade_level_id = Column(Integer, ForeignKey("grade_levels.id", ondelete="CASCADE"), nullable=False, index=True)
 
    # Assigned teacher (set by admin)
    teacher_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True, index=True)

    # relationship sa grade level
    grade_level = relationship("GradeLevels", back_populates="sections")

    # assigned teacher relationship
    teacher = relationship("Accounts", foreign_keys=[teacher_id])

    # student profile relationship
    students = relationship("StudentProfile", back_populates="section")

    # teacher class relationship
    teacher_classes = relationship("TeacherClass", back_populates="sections")