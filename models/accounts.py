from sqlalchemy import String, Integer, Column, DateTime, Enum
from sqlalchemy.orm import relationship
from database.connection import Base
from utils.enum import RoleEnum
from utils.utc_now import utc_now

class Accounts(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String(50), unique=True, nullable=True, index=True)
    # username for students only

    email = Column(String(50), unique=True, nullable=True, index=True)
    # email only for teacher and admin
    
    hashed_password = Column(String(255), nullable=False)

    role = Column(Enum(RoleEnum), default=RoleEnum.student, nullable=False)
    # Student | Teacher | Admin
    
    # one to one relationship sa student profile table
    student_profile = relationship("StudentProfile", back_populates="student_account", passive_deletes=True, uselist=False)

    # student/teacher(owner_id) file relationship one to many
    files = relationship("FileUpload", back_populates="account", passive_deletes=True)

    # one to one relationship sa teacher profile table
    teacher_profile = relationship("TeacherProfile", back_populates="teacher_account", passive_deletes=True, uselist=False)

    # teacher classes one to many relationship
    teacher_classes = relationship("TeacherClass", back_populates="teacher_account", passive_deletes=True)

    # teacher modules one to many relationship
    teacher_modules = relationship("TeacherModule", back_populates="teacher_account", passive_deletes=True)

    # teacher quiz/activity assessments one to many relationship
    teacher_assessments = relationship("TeacherAssessment", back_populates="teacher_account", passive_deletes=True)

    topic_progress = relationship("StudentTopicProgress", passive_deletes=True)
    quiz_progress = relationship("StudentQuizProgress", passive_deletes=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


