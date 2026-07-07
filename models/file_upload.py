from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from database.connection import Base
from utils.utc_now import utc_now
from utils.enum import FileCategory

class FileUpload(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, unique=True, index=True)

    filename = Column(String(255), nullable=False)

    file_type = Column(String(255), nullable=False)

    file_url = Column(String(255), nullable=False)

    public_id = Column(String(255), nullable=False)

    file_category = Column(Enum(FileCategory), nullable=False)

    # account relationship one to many
    owner_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)

    account = relationship("Accounts", back_populates="files")

    # student profile one to one relationship image upload(profile)
    student_image = relationship("StudentProfile", back_populates="image_file", passive_deletes=True, uselist=False)

    # teacher profile one to one relationship image upload(profile)
    teacher_image = relationship("TeacherProfile", back_populates="image_file", passive_deletes=True, uselist=False)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


