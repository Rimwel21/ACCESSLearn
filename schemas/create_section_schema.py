from pydantic import BaseModel,Field ,model_validator, field_validator

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
            data["name"] = value.strip()

        return data
    
    @field_validator("name")
    @classmethod
    def validate_section_name(cls, value:str):
        if value is None:
            raise ValueError("section name cannot be empty")
        
        if not value[0].isupper():
            raise ValueError("section name must start with uppercase letter.")
        
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