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
    if not expected_answer or not recognized_answer:
        return False

    raw_expected = str(expected_answer).strip()
    raw_recognized = str(recognized_answer).strip()

    # Check if expected_answer is an encoded Multiple Choice string (e.g. "A:Leaf|B:Stem|CORRECT:B")
    if "CORRECT:" in raw_expected and "|" in raw_expected:
        parts = raw_expected.split("|")
        correct_letter = ""
        choice_map: dict[str, str] = {}
        for part in parts:
            if ":" in part:
                k, v = part.split(":", 1)
                k = k.strip()
                v = v.strip()
                if k == "CORRECT":
                    correct_letter = v.upper()
                elif k:
                    choice_map[k.upper()] = v

        correct_text = choice_map.get(correct_letter, "")
        rec_upper = raw_recognized.upper()

        if rec_upper == correct_letter:
            return True
        if correct_text and normalize_answer(raw_recognized) == normalize_answer(correct_text):
            return True
        if correct_text and canonicalize_answer(raw_recognized) and canonicalize_answer(raw_recognized) == canonicalize_answer(correct_text):
            return True
        return False

    # True or False handling
    exp_up = raw_expected.upper()
    if exp_up in {"TRUE", "FALSE"}:
        rec_up = raw_recognized.upper()
        if rec_up == exp_up:
            return True
        if exp_up == "TRUE" and rec_up in {"T", "YES"}:
            return True
        if exp_up == "FALSE" and rec_up in {"F", "NO"}:
            return True

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

