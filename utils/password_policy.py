import re

from pydantic_core import PydanticCustomError


COMMON_PASSWORDS = {
    "12345678",
    "password",
    "password1",
    "qwerty123",
    "signhear",
}


def validate_new_password(value: str) -> str:
    if value != value.strip():
        raise PydanticCustomError("password_whitespace", "Password cannot start or end with spaces")
    if len(value) < 8 or len(value) > 72:
        raise PydanticCustomError("password_length", "Password must be between 8 and 72 characters")
    if any(character.isspace() for character in value):
        raise PydanticCustomError("password_whitespace", "Password cannot contain spaces")
    if value.lower() in COMMON_PASSWORDS:
        raise PydanticCustomError("password_common", "Choose a less common password")
    if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
        raise PydanticCustomError("password_strength", "Password must contain at least one letter and one number")
    return value
