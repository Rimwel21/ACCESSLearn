import pickle
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

from core.handsign_config import HandSignSettings, get_handsign_settings
from services.handsign.word_scoring_service import nearest_competing_reference, score_sequence
from utils.handsign.image import decode_base64_image
from utils.handsign.science_vocabulary import canonical_word
from utils.handsign.word_gesture_features import holistic_result_to_feature_vector, resample_sequence


def _settings(settings: HandSignSettings | None = None) -> HandSignSettings:
    return settings or get_handsign_settings()


MIN_HAND_FRAME_RATIO = 0.60
MIN_HAND_MOTION = 0.025
PASS_SIMILARITY_PERCENT = 70.0
COMPETING_DISTANCE_RATIO = 0.90


def _frame_sequence_with_quality(images: list[str]) -> tuple[list[list[float]], dict[str, float]]:
    """Turn browser camera frames into the same landmark sequence used for training."""
    if not images:
        raise ValueError("At least one frame is required.")

    import mediapipe as mp

    mp_holistic = mp.solutions.holistic
    sequence = []
    detected_frames = 0
    hand_frames = 0
    hand_positions: list[np.ndarray] = []
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
            hands = [hand.landmark[0] for hand in (result.left_hand_landmarks, result.right_hand_landmarks) if hand]
            if hands:
                hand_frames += 1
                hand_positions.append(np.mean([[point.x, point.y, point.z] for point in hands], axis=0))

    if detected_frames == 0:
        raise ValueError("No body or hand landmarks were detected in the captured attempt.")
    movement = 0.0
    if len(hand_positions) > 1:
        movement = float(np.mean(np.linalg.norm(np.diff(np.asarray(hand_positions), axis=0), axis=1)))
    return sequence, {"hand_frame_ratio": hand_frames / len(images), "hand_motion": movement}


def _frame_sequence(images: list[str]) -> list[list[float]]:
    return _frame_sequence_with_quality(images)[0]


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


def assess_frame_sequence(word: str, images: list[str]) -> dict[str, float | bool | str]:
    """Strict word-gesture assessment used for scored student responses."""
    target_word = canonical_word(word)
    sequence, quality = _frame_sequence_with_quality(images)
    score = score_sequence(target_word, sequence)
    similarity = float(score["score"])

    if quality["hand_frame_ratio"] < MIN_HAND_FRAME_RATIO:
        return {
            "correct": False,
            "similarity_percent": round(similarity, 2),
            "feedback": "Keep at least one hand clearly visible to the camera for the full sign.",
        }
    if quality["hand_motion"] < MIN_HAND_MOTION:
        return {
            "correct": False,
            "similarity_percent": round(similarity, 2),
            "feedback": "Show the complete word gesture with clear hand movement before checking.",
        }

    competitor = nearest_competing_reference(target_word, sequence)
    target_distance = float(score["target_distance"])
    closer_than_other_words = competitor is None or target_distance <= float(competitor["distance"]) * COMPETING_DISTANCE_RATIO
    if similarity < PASS_SIMILARITY_PERCENT:
        feedback = "Your sign is not close enough to the saved reference samples yet. Try the full gesture again."
    elif not closer_than_other_words:
        feedback = "This gesture looks closer to a different saved word. Review the guide video and try again."
    else:
        feedback = "Correct sign! Your answer has been recorded."

    return {
        "correct": similarity >= PASS_SIMILARITY_PERCENT and closer_than_other_words,
        "similarity_percent": round(similarity, 2),
        "feedback": feedback,
    }


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
