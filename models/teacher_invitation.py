"""
TeacherInvitation model.

Lifecycle: pending → accepted / expired / cancelled
Admin creates the invitation; the teacher clicks the link and completes onboarding.
"""
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from database.connection import Base
from utils.enum import InvitationStatusEnum
from utils.utc_now import utc_now


class TeacherInvitation(Base):
    __tablename__ = "teacher_invitations"

    id = Column(Integer, primary_key=True, index=True)

    # Recipient details captured at invite-time
    full_name   = Column(String(100), nullable=False)
    email       = Column(String(100), nullable=False, index=True)
    contact_no  = Column(String(25), nullable=True)

    # Secure activation token (stored as raw UUID; hash on validation side if needed)
    token       = Column(String(255), unique=True, nullable=False, index=True)

    status = Column(
        Enum(InvitationStatusEnum),
        default=InvitationStatusEnum.pending,
        nullable=False,
        index=True,
    )

    # Admin who sent the invite
    invited_by = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)

    # Account created after teacher completes onboarding (nullable until accepted)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True, unique=True)

    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Optional note the admin added when resending
    resend_note = Column(Text, nullable=True)

    created_at  = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at  = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
