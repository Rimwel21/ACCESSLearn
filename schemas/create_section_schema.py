from pydantic import BaseModel, Field, field_validator, model_validator


def normalize_section_name(value: str) -> str:
    value = " ".join(value.strip().split())
    if not value:
        return value
    return value[0].upper() + value[1:]

class SectionBase(BaseModel):
    name: str 
    grade_level_id: int

    @model_validator(mode="before")
    @classmethod
    def sanitize_section_name(cls, data):
        if not isinstance(data, dict):
            return data

        value = data.get("name")
        if isinstance(value, str):
            data["name"] = normalize_section_name(value)

        return data
    
    @field_validator("name")
    @classmethod
    def validate_section_name(cls, value:str):
        if value is None or not value.strip():
            raise ValueError("section name cannot be empty")

        return value

class SectionCreate(SectionBase):
    pass

class GradeLevelResponse(BaseModel):
    name: str

    class Config:
        from_attributes = True

class SectionOut(BaseModel):
    name: str
    grade_level: GradeLevelResponse
