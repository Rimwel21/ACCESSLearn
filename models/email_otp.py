from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from database.connection import Base
from utils.utc_now import utc_now
from utils.enum import RoleEnum, VerificationStatus

class EmailOTP(Base):
    __tablename__ = "email_otps"

    id = Column(Integer, primary_key=True, unique=True, index=True, nullable=False)

    email = Column(String(255), nullable=False)

    role = Column(Enum(RoleEnum), nullable=False)

    otp_hash = Column(String(255), nullable=False)

    verification_status = Column(Enum(VerificationStatus), default=VerificationStatus.pending, nullable=False)

    is_used = Column(Boolean, default=False, nullable=False)
    attempt_count = Column(Integer, default=0, nullable=False)

    expired_at = Column(DateTime(timezone=True), nullable=False)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)