from enum import Enum

# Role Enum (Student, Teacher, Admin):
class RoleEnum(str, Enum):
    student = "student"
    teacher = "teacher"
    admin = "admin"
    
# student type enum:
class StudentType(str, Enum):
    regular = "regular"
    HI = "hearing impaired"

class UserSex(str, Enum):
    Male = "Male"
    Female = "Female"

class GradeLevel(str, Enum):
    grade_1 = "grade_1"
    grade_2 = "grade_2"
    grade_3 = "grade_3"
    grade_4 = "grade_4"
    grade_5 = "grade_5"
    grade_6 = "grade_6"

class FileCategory(str, Enum):
    PROFILE_IMAGE = "PROFILE_IMAGE"
    LEARNING_MATERIAL = "LEARNING_MATERIAL"
