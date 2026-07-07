from pydantic import BaseModel
from datetime import datetime
from utils.enum import FileCategory

class FileOut(BaseModel):
    id: int
    filename: str
    file_type: str
    file_url: str
    file_category: FileCategory
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProfileImageOut(BaseModel):
    id: int | None = None
    filename: str
    file_type: str
    file_url: str
    file_category: FileCategory
    is_default: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
