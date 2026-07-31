from pydantic import BaseModel


class GradeLevelOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class SectionOut(BaseModel):
    id: int
    name: str
    grade_level_id: int

    class Config:
        from_attributes = True
