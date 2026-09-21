from pydantic import BaseModel, Field


class WordGestureSampleCreate(BaseModel):
    label: str = Field(min_length=1, max_length=80)
    week: str | None = Field(default=None, max_length=30)
    images: list[str] = Field(min_length=40, max_length=40)


class DatasetLabelCreate(BaseModel):
    label: str = Field(min_length=1, max_length=80)
    week: str = Field(min_length=1, max_length=30)


class DatasetWeekCreate(BaseModel):
    week: str = Field(min_length=1, max_length=30)

