from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from utils.utc_now import utc_now
from utils.enum import UserSex
from database.connection import Base

class TeacherProfile(Base):
    __tablename__ = "teacher_profiles"

    id = Column(Integer, primary_key=True, nullable=False, index=True)

    # one to one relationship sa accounts table
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    teacher_account = relationship("Accounts", back_populates="teacher_profile")

    # one to one relationship sa file table
    profile_image_id = Column(Integer, ForeignKey("files.id", ondelete="SET NULL"), unique=True, nullable=True, index=True)

    image_file = relationship("FileUpload", back_populates="teacher_image")

    name = Column(String(50), nullable=False)

    age = Column(Integer, default=0, nullable=True)

    sex = Column(Enum(UserSex), nullable=True)

    handle_grade_levels = relationship("TeacherGradeHandles", back_populates="teacher", passive_deletes=True)

    contact_no = Column(String(20), nullable=False)

    email_address = Column(String(50), nullable=False, unique=True)

    address = Column(String(50), nullable=False)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
