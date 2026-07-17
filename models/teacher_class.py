from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from database.connection import Base
from utils.utc_now import utc_now


class TeacherClass(Base):
    __tablename__ = "teacher_classes"

    id = Column(Integer, primary_key=True, nullable=False, index=True)

    teacher_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_account = relationship("Accounts", back_populates="teacher_classes")
    modules = relationship("TeacherModule", back_populates="teacher_class", passive_deletes=True)

    class_name = Column(String(120), nullable=False, default="Class")
    subject = Column(String(120), nullable=False, default="General")

    grade_level_id = Column(Integer, ForeignKey("grade_levels.id"), nullable=False, index=True)
    grade_levels = relationship("GradeLevels", back_populates="teacher_classes")

    section_id = Column(Integer, ForeignKey("hi_sections.id"), nullable=False, index=True)
    sections = relationship("HI_SECTIONS", back_populates="teacher_classes")

    school_year = Column(String(30), nullable=True)
    student_count = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("teacher_id", "subject", "grade_level_id", "section_id", name="uq_teacher_class_subject_grade_section"),
    )
