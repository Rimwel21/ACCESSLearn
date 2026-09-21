from sqlalchemy import Column, DateTime, Integer, String

from database.connection import Base
from utils.utc_now import utc_now


class HandsignDatasetWeek(Base):
    __tablename__ = "handsign_dataset_weeks"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    key = Column(String(10), nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
