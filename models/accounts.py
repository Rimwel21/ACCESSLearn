from sqlalchemy import String, Integer, Column, DateTime, Enum, Boolean
from sqlalchemy.orm import relationship
from database.connection import Base
from utils.enum import RoleEnum, AccountStatusEnum
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

    # Full account lifecycle status (admin-controlled)
    account_status = Column(
        Enum(AccountStatusEnum),
        default=AccountStatusEnum.active,
        nullable=False,
        index=True,
    )

    # one to one relationship sa student profile table
    student_profile = relationship("StudentProfile", back_populates="student_account", passive_deletes=True, uselist=False)

    # teacher(owner_id) file relationship one to many for learning materials
    files = relationship("FileUpload", back_populates="account", passive_deletes=True)

    # one to one relationship sa teacher profile table
    teacher_profile = relationship("TeacherProfile", back_populates="teacher_account", passive_deletes=True, uselist=False)

    # ─── Admin relationships ────────────────────────────────────────────────
    notifications_received = relationship(
        "Notification", foreign_keys="Notification.recipient_id",
        back_populates="recipient", passive_deletes=True
    )
    audit_logs = relationship(
        "AuditLog", foreign_keys="AuditLog.user_id",
        back_populates="actor", passive_deletes=True
    )

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
