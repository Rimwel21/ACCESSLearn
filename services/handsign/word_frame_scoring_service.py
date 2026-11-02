import pickle
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

from core.handsign_config import HandSignSettings, get_handsign_settings
from services.handsign.word_scoring_service import score_sequence
from utils.handsign.image import decode_base64_image
from utils.handsign.science_vocabulary import canonical_word
from utils.handsign.word_gesture_features import holistic_result_to_feature_vector, resample_sequence


def _settings(settings: HandSignSettings | None = None) -> HandSignSettings:
    return settings or get_handsign_settings()


def _frame_sequence(images: list[str]) -> list[list[float]]:
    """Turn browser camera frames into the same landmark sequence used for training."""
    if not images:
        raise ValueError("At least one frame is required.")

    import mediapipe as mp

    mp_holistic = mp.solutions.holistic
    sequence = []
    detected_frames = 0
    with mp_holistic.Holistic(
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        min_detection_confidence=0.3,
        min_tracking_confidence=0.4,
    ) as holistic:
        for image in images:
            frame = decode_base64_image(image)
            result = holistic.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            if result.pose_landmarks or result.left_hand_landmarks or result.right_hand_landmarks:
                detected_frames += 1
            sequence.append(holistic_result_to_feature_vector(result))

    if detected_frames == 0:
        raise ValueError("No body or hand landmarks were detected in the captured attempt.")
    return sequence


@lru_cache(maxsize=2)
def _load_word_classifier(model_path: str, modified_at_ns: int):
    """Cache the published classifier and refresh it after Admin publishes a replacement."""
    del modified_at_ns
    with Path(model_path).open("rb") as file:
        return pickle.load(file)


def score_frame_sequence(word: str, images: list[str]) -> dict:
    if not images:
        raise ValueError("At least one frame is required.")

    # Reference similarity uses the saved Admin samples directly. It does not
    # require the separate multi-class classifier to have been trained/published.
    return score_sequence(canonical_word(word), _frame_sequence(images))


def predict_frame_sequence(
    images: list[str],
    expected_word: str | None = None,
    settings: HandSignSettings | None = None,
) -> dict[str, float | str]:
    """Predict the signed word from all Admin Word Gesture classes.

    The caller intentionally receives the label only on the server; student routes
    should compare it to the expected answer and return a simple correct/incorrect result.
    """
    config = _settings(settings)
    model_path = config.resolved_word_gesture_model_path()
    if not model_path.exists():
        raise RuntimeError("The Admin Word Gesture model has not been trained yet.")

    classifier = _load_word_classifier(str(model_path), model_path.stat().st_mtime_ns)
    if not hasattr(classifier, "predict_proba") or not hasattr(classifier, "classes_"):
        raise RuntimeError("The published Admin Word Gesture model is invalid. Train it again.")

    sequence = _frame_sequence(images)
    features = resample_sequence(sequence, config.word_sequence_length).reshape(1, -1)
    probabilities = classifier.predict_proba(np.asarray(features, dtype=np.float32))[0]
    predicted_index = int(np.argmax(probabilities))
    result: dict[str, float | str] = {
        "predicted_word": canonical_word(str(classifier.classes_[predicted_index])),
        "confidence": float(probabilities[predicted_index]),
    }
    if expected_word is not None:
        target_word = canonical_word(expected_word)
        matching_probabilities = [
            float(probability)
            for label, probability in zip(classifier.classes_, probabilities)
            if canonical_word(str(label)) == target_word
        ]
        result["expected_confidence"] = float(sum(matching_probabilities))
    return result
