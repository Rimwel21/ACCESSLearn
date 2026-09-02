import re


SUPPORTED_SCIENCE_SIGNS = [
    "EARTH",
    "SUN",
    "MOON",
    "WATER",
    "OXYGEN",
    "PLANT",
    "ANIMAL",
    "GRAVITY",
    "ENERGY",
    "LIGHT",
    "HEAT",
    "SOLID",
    "LIQUID",
    "GAS",
    "FORCE",
    "PUSH",
    "PULL",
    "AIR",
]

ANSWER_ALIASES = {
    "EARTH": ["EARTH", "THE EARTH", "WORLD"],
    "SUN": ["SUN", "THE SUN"],
    "MOON": ["MOON", "THE MOON"],
    "WATER": ["WATER", "H2O"],
    "OXYGEN": ["OXYGEN", "O2"],
    "PLANT": ["PLANT", "PLANTS"],
    "ANIMAL": ["ANIMAL", "ANIMALS"],
    "GRAVITY": ["GRAVITY"],
    "ENERGY": ["ENERGY"],
    "LIGHT": ["LIGHT"],
    "HEAT": ["HEAT"],
    "SOLID": ["SOLID"],
    "LIQUID": ["LIQUID"],
    "GAS": ["GAS"],
    "FORCE": ["FORCE"],
    "PUSH": ["PUSH"],
    "PULL": ["PULL"],
    "AIR": ["AIR"],
}


def normalize_answer(answer: str | None) -> str:
    normalized = str(answer or "").upper().replace("_", " ")
    normalized = re.sub(r"[^A-Z0-9 ]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def canonicalize_answer(answer: str | None) -> str | None:
    normalized = normalize_answer(answer)
    if not normalized:
        return None

    for canonical, aliases in ANSWER_ALIASES.items():
        if normalized in {normalize_answer(alias) for alias in aliases}:
            return canonical

    direct_label = normalized.replace(" ", "_")
    if direct_label in SUPPORTED_SCIENCE_SIGNS:
        return direct_label
    return None


def canonical_word(word: str | None) -> str:
    return canonicalize_answer(word) or normalize_answer(word).replace(" ", "_")


def answers_match(recognized_answer: str | None, expected_answer: str | None) -> bool:
    expected = canonicalize_answer(expected_answer)
    recognized = canonicalize_answer(recognized_answer)
    if expected is not None or recognized is not None:
        return expected is not None and expected == recognized
    return normalize_answer(expected_answer) == normalize_answer(recognized_answer)


def validate_recognized_answer(recognized_answer: str | None, expected_answer: str | None) -> dict[str, str | bool | None]:
    expected = canonicalize_answer(expected_answer)
    recognized = canonicalize_answer(recognized_answer)
    return {
        "expected_canonical": expected,
        "recognized_canonical": recognized,
        "is_correct": answers_match(recognized_answer, expected_answer),
    }
