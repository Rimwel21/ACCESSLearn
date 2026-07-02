from pydantic import BaseModel, field_validator, model_validator, Field
from utils.enum import StudentType, GradeLevel, UserSex
from datetime import datetime

class StudentProfileBase(BaseModel):
    name: str = Field(min_length=5, max_length=100)
    age: int
    sex: UserSex
    grade_level: GradeLevel
    section: str
    student_type: StudentType
    guardians_name: str | None = None
    guardians_contact_no: str | None = None
    address: str | None = None

    @model_validator(mode="before")
    @classmethod
    def data_strip(cls, data):
        if not isinstance(data, dict):
            return data
        
        fields = ["name", "section", "guardians_name", "guardians_contact_no", "address"]
        
        for field in fields:
            value = data.get(field)

            if isinstance(value, str):
                data[field] = value.strip()

        return data
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, value:str):
        
        if not value:
            raise ValueError("Name cannot be empty")
        
        if not value[0].isupper():
            raise ValueError("Name must start with an uppercase letter.")
        
        return value
    
    @field_validator("guardians_name")
    @classmethod
    def validate_guardians_name(cls, value:str):
        
        if value:
            if not value[0].isupper():
                raise ValueError("Guardians name must start with an uppercase letter.")
        
        return value
    
    @field_validator("guardians_contact_no")
    @classmethod
    def validate_guardians_contact_no(cls, value:str):

        if not value.isdigit():
            raise ValueError("Contact number must contain only numbers.")

        if not value.startswith("0"):
            raise ValueError("Contact number must start with 0.")
        
        if len(value) != 11:
            raise ValueError("Contact number consists of 11 numbers.")

        return value
    
class StudentProfileCreate(StudentProfileBase):
    pass

class StudentProfileUpdate(BaseModel):
    name: str | None = None
    age: int | None = None
    sex: UserSex | None = None
    grade_level: GradeLevel | None = None
    section: str | None = None
    student_type: StudentType | None = None
    guardians_name: str | None = None
    guardians_contact_no: str | None = None
    address: str | None = None

    @model_validator(mode="before")
    @classmethod
    def data_strip(cls, data):
        if not isinstance(data, dict):
            return data
        
        fields = ["name", "section", "guardians_name", "guardians_contact_no", "address"]
        
        for field in fields:
            value = data.get(field)

            if isinstance(value, str):
                data[field] = value.strip()

        return data
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, value:str):
        
        if value is None:
            return value
        
        if not value[0].isupper():
            raise ValueError("Name must start with an uppercase letter.")
        
        return value
    
    @field_validator("guardians_name")
    @classmethod
    def validate_guardians_name(cls, value:str):
        if value is None:
            return value

        if value:
            if not value[0].isupper():
                raise ValueError("Guardians name must start with an uppercase letter.")
        
        return value
    
    @field_validator("guardians_contact_no")
    @classmethod
    def validate_guardians_contact_no(cls, value:str):

        if value is None:
            return value

        if not value.isdigit():
            raise ValueError("Contact number must contain only numbers.")

        if not value.startswith("0"):
            raise ValueError("Contact number must start with 0.")
        
        if len(value) != 11:
            raise ValueError("Contact number consists of 11 numbers.")

        return value

class StudentProfileOut(BaseModel):
    id: int
    name: str
    age: int
    sex: UserSex
    grade_level: GradeLevel
    section: str
    student_type: StudentType
    account_id: int
    profile_image_id: int | None = None
    guardians_name: str | None = None
    guardians_contact_no: str | None = None
    address: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True