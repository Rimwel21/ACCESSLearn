from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
from database.connection import Base
from utils.utc_now import utc_now
from utils.enum import StudentType, GradeLevel, UserSex

class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    age = Column(Integer, nullable=True) # made nullable to support multi-step setup
    sex = Column(Enum(UserSex), nullable=True) # made nullable to support multi-step setup
    student_type = Column(Enum(StudentType), nullable=True) # made nullable to support multi-step setup

    # Legacy fields kept for backward-compatibility but made nullable
    grade_level = Column(String(100), nullable=True)
    section = Column(String(250), nullable=True)

    # New FK relations
    grade_level_id = Column(Integer, ForeignKey("grade_levels.id", ondelete="SET NULL"), nullable=True, index=True)
    section_id     = Column(Integer, ForeignKey("sections.id", ondelete="SET NULL"), nullable=True, index=True)

    # Relationships
    assigned_section = relationship("Section", back_populates="students")
    assigned_grade   = relationship("GradeLevel")

    # one to one relationship sa accounts table
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    student_account = relationship("Accounts", back_populates="student_profile")

    # one to one relationship sa file table
    profile_image_id = Column(Integer, ForeignKey("files.id", ondelete="SET NULL"), unique=True, nullable=True, index=True)
    image_file = relationship("FileUpload", back_populates="student_image")

    guardians_name = Column(String, nullable=True)
    guardians_contact_no = Column(String(20), nullable=True)
    address = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
