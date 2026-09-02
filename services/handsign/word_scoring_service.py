from pathlib import Path

import numpy as np

from core.handsign_config import HandSignSettings, get_handsign_settings
from utils.handsign.science_vocabulary import canonical_word
from utils.handsign.word_gesture_features import resample_sequence


def _settings(settings: HandSignSettings | None = None) -> HandSignSettings:
    return settings or get_handsign_settings()


def target_reference_paths(word: str, settings: HandSignSettings | None = None) -> list[Path]:
    config = _settings(settings)
    word_dir = config.resolved_word_gesture_dataset_path() / canonical_word(word)
    return sorted(word_dir.glob("*.npz"))


def load_target_references(word: str, settings: HandSignSettings | None = None) -> np.ndarray:
    config = _settings(settings)
    references = []
    for path in target_reference_paths(word, config):
        data = np.load(path)
        references.append(resample_sequence(data["sequence"], config.word_sequence_length))
    if not references:
        target = canonical_word(word)
        raise ValueError(f"No landmark samples found for {target}.")
    return np.asarray(references, dtype=np.float32)


def target_distance_threshold(references: np.ndarray) -> float:
    if len(references) < 2:
        return 1.0

    distances = []
    for index, sequence in enumerate(references):
        others = np.delete(references, index, axis=0)
        nearest = float(np.min(np.mean(np.linalg.norm(others - sequence, axis=2), axis=1)))
        distances.append(nearest)

    threshold = float(np.percentile(distances, 75))
    return max(threshold, 1e-6)


def score_sequence(word: str, sequence: list[list[float]], settings: HandSignSettings | None = None) -> dict[str, float | int | str]:
    config = _settings(settings)
    target_word = canonical_word(word)
    references = load_target_references(target_word, config)
    threshold = target_distance_threshold(references)
    normalized_sequence = resample_sequence(sequence, config.word_sequence_length)
    distances = np.mean(np.linalg.norm(references - normalized_sequence, axis=2), axis=1)
    nearest_index = int(np.argmin(distances))
    nearest_distance = float(distances[nearest_index])
    score = 100.0 * np.exp(-max(0.0, nearest_distance - threshold) / (threshold * 1.5))

    return {
        "target_word": target_word,
        "nearest_reference_index": nearest_index + 1,
        "target_distance": nearest_distance,
        "target_distance_threshold": threshold,
        "score": round(float(np.clip(score, 0.0, 100.0)), 2),
    }
