import json
from pathlib import Path

from core.handsign_config import HandSignSettings, get_handsign_settings
from utils.handsign.science_vocabulary import canonical_word


def _settings(settings: HandSignSettings | None = None) -> HandSignSettings:
    return settings or get_handsign_settings()


def list_dataset_classes(settings: HandSignSettings | None = None) -> list[dict[str, int | str]]:
    dataset_dir = _settings(settings).resolved_word_gesture_dataset_path()
    if not dataset_dir.exists():
        return []

    classes = []
    for directory in sorted(path for path in dataset_dir.iterdir() if path.is_dir()):
        sample_count = len(list(directory.glob("*.npz")))
        classes.append({"label": directory.name, "sample_count": sample_count})
    return classes


def load_word_model_metadata(settings: HandSignSettings | None = None) -> dict | None:
    config = _settings(settings)
    candidate_paths: list[Path] = [
        config.resolved_word_gesture_metadata_path(),
        config.resolved_model_base_path() / "word_gesture_metadata.json",
        config.resolved_model_base_path() / "sign_model_metadata.json",
        config.resolved_model_base_path() / "class_indices.json",
    ]
    for path in candidate_paths:
        if path.exists():
            with open(path, "r", encoding="utf-8") as file:
                return json.load(file)
    return None


def trained_word_classes(settings: HandSignSettings | None = None) -> set[str]:
    metadata = load_word_model_metadata(settings)
    if not metadata:
        return set()
    classes = metadata.get("classes", [])
    if isinstance(classes, dict):
        classes = classes.keys()
    return {canonical_word(str(label)) for label in classes}


def is_word_trained(word: str, settings: HandSignSettings | None = None) -> bool:
    return canonical_word(word) in trained_word_classes(settings)


def word_gesture_summary(settings: HandSignSettings | None = None) -> dict:
    config = _settings(settings)
    return {
        "dataset_dir": str(config.resolved_word_gesture_dataset_path()),
        "classes": list_dataset_classes(config),
        "model_metadata": load_word_model_metadata(config),
        "trained_classes": sorted(trained_word_classes(config)),
    }
