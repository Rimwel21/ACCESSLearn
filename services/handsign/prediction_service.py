import json
import logging
import os
import pickle
import threading
import time
from collections import deque
from pathlib import Path

import cv2
import numpy as np

from core import handsign_recognition as recognition
from core.handsign_config import HandSignSettings
from models.handsign.prediction import BoundingBox, PredictionResult
from utils.handsign.landmark_features import FEATURE_VERSION, feature_length, landmarks_to_feature_vector

logger = logging.getLogger(__name__)


def apply_prediction(prediction: str, confirmed_text: str) -> str:
    if prediction == "space":
        return confirmed_text + " "
    if prediction == "del":
        return confirmed_text[:-1]
    if prediction == "nothing":
        return confirmed_text
    return confirmed_text + prediction


def weighted_average_probabilities(history) -> np.ndarray:
    probabilities = np.asarray(history)
    weights = np.linspace(1.0, 2.0, len(probabilities), dtype=np.float32)
    return np.average(probabilities, axis=0, weights=weights)


def normalized_landmark_points(landmarks) -> np.ndarray:
    points = np.asarray([[float(point.x), float(point.y)] for point in landmarks], dtype=np.float32)
    centered = points - points[0]
    scale = float(np.max(np.linalg.norm(centered[1:], axis=1)))
    if scale < 1e-6:
        scale = 1.0
    return centered / scale


def hand_scale_from_landmarks(landmarks) -> float:
    points = np.asarray([[float(point.x), float(point.y)] for point in landmarks], dtype=np.float32)
    span = np.ptp(points, axis=0)
    scale = float(max(span[0], span[1]))
    if scale < 1e-6:
        scale = 1.0
    return scale


def class_probability(proba: np.ndarray, classes: np.ndarray, label: str) -> float:
    matches = np.where(classes == label)[0]
    if len(matches) == 0:
        return 0.0
    return float(proba[int(matches[0])])


def top_labels(proba: np.ndarray, classes: np.ndarray, count: int = 3) -> list[tuple[str, float]]:
    indices = np.argsort(proba)[-count:][::-1]
    return [(str(classes[index]), float(proba[index])) for index in indices]


def path_length(points: np.ndarray) -> float:
    if len(points) < 2:
        return 0.0
    return float(np.sum(np.linalg.norm(np.diff(points, axis=0), axis=1)))


def finger_extension(normalized: np.ndarray, tip: int, mcp: int) -> float:
    return float(np.linalg.norm(normalized[tip] - normalized[mcp]))


def is_m_family_shape(normalized: np.ndarray) -> bool:
    index = finger_extension(normalized, 8, 5)
    middle = finger_extension(normalized, 12, 9)
    ring = finger_extension(normalized, 16, 13)
    pinky = finger_extension(normalized, 20, 17)
    return (
        normalized[8, 1] > -0.10
        and normalized[12, 1] > 0.00
        and max(index, middle, ring, pinky) > 0.45
    )


def is_p_family_shape(normalized: np.ndarray) -> bool:
    index = finger_extension(normalized, 8, 5)
    middle = finger_extension(normalized, 12, 9)
    ring = finger_extension(normalized, 16, 13)
    pinky = finger_extension(normalized, 20, 17)
    return (
        0.32 <= index <= 0.90
        and 0.25 <= middle <= 0.85
        and ring <= 0.70
        and pinky <= 0.65
        and normalized[12, 1] > -0.35
    )


def calibrate_static_problem_prediction(
    prediction: str,
    confidence: float,
    averaged_proba: np.ndarray,
    classes: np.ndarray,
    landmarks,
) -> tuple[str, float, str | None]:
    normalized = normalized_landmark_points(landmarks)
    labels = top_labels(averaged_proba, classes)
    top_label, top_confidence = labels[0]

    m_probability = class_probability(averaged_proba, classes, "M")
    if (
        prediction == "M"
        and m_probability >= recognition.M_CALIBRATION_MIN_PROBABILITY
        and is_m_family_shape(normalized)
    ):
        return "M", max(confidence, recognition.STATIC_CALIBRATION_CONFIDENCE), "calibrated M"

    p_probability = class_probability(averaged_proba, classes, "P")
    p_is_close = top_confidence - p_probability <= recognition.P_CALIBRATION_CLOSE_MARGIN
    p_in_top_labels = any(label == "P" for label, _ in labels)
    if (
        p_probability >= recognition.P_CALIBRATION_MIN_PROBABILITY
        and p_in_top_labels
        and (top_label == "P" or (top_label in recognition.P_RELATED_LABELS and p_is_close))
        and is_p_family_shape(normalized)
    ):
        return "P", max(confidence, recognition.STATIC_CALIBRATION_CONFIDENCE), "calibrated P"

    return prediction, confidence, None


def maybe_reset_history_for_new_sign(history, proba: np.ndarray, classes: np.ndarray, threshold: float) -> None:
    if not history:
        return

    previous_proba = weighted_average_probabilities(history)
    previous_index = int(np.argmax(previous_proba))
    current_index = int(np.argmax(proba))
    if classes[previous_index] == classes[current_index]:
        return

    current_confidence = float(proba[current_index])
    previous_support_for_current = float(previous_proba[current_index])
    if (
        current_confidence >= threshold
        and current_confidence - previous_support_for_current >= recognition.SIGN_CHANGE_RESET_MARGIN
    ):
        history.clear()


class DynamicGestureTracker:
    def __init__(
        self,
        window_seconds: float,
        min_frames: int,
        primary_probabilities: dict[str, float],
        secondary_probability: float,
        cooldown_seconds: float,
        direct_frames: int,
    ) -> None:
        self.window_seconds = window_seconds
        self.min_frames = min_frames
        self.direct_frames = direct_frames
        self.primary_probabilities = dict(primary_probabilities)
        self.secondary_probability = secondary_probability
        self.cooldown_seconds = cooldown_seconds
        self.observations = deque()
        self.last_accepted_at = -cooldown_seconds
        self.locked_label: str | None = None

    def reset(self, clear_lock: bool = True) -> None:
        self.observations.clear()
        if clear_lock:
            self.locked_label = None

    def reset_label(self, label: str) -> None:
        if label not in recognition.DYNAMIC_GESTURE_LABELS:
            return

        self.observations.clear()
        if self.locked_label == label:
            self.locked_label = None
        self.last_accepted_at = -self.cooldown_seconds

    def update(self, landmarks, proba: np.ndarray, classes: np.ndarray, now: float) -> tuple[str | None, float]:
        points = np.asarray([[float(point.x), float(point.y)] for point in landmarks], dtype=np.float32)
        normalized = normalized_landmark_points(landmarks)
        scale = hand_scale_from_landmarks(landmarks)
        top_label = str(classes[int(np.argmax(proba))])

        self.observations.append(
            {
                "time": now,
                "index_tip": points[8],
                "pinky_tip": points[20],
                "scale": scale,
                "j_probability": class_probability(proba, classes, "J"),
                "z_probability": class_probability(proba, classes, "Z"),
                "top_label": top_label,
                "index_shape": self._index_shape(normalized),
                "pinky_shape": self._pinky_shape(normalized),
            }
        )

        while self.observations and now - self.observations[0]["time"] > self.window_seconds:
            self.observations.popleft()

        if self.locked_label is not None:
            if now - self.last_accepted_at < self.cooldown_seconds:
                return None, 0.0
            if self._gesture_still_active(self.locked_label):
                return None, 0.0

            self.locked_label = None
            self.reset(clear_lock=False)
            return None, 0.0

        if now - self.last_accepted_at < self.cooldown_seconds:
            return None, 0.0

        candidates = []
        direct_j_confidence = self._detect_direct_dynamic_label("J", "pinky_shape", {"J", "I", "Y"})
        if direct_j_confidence is not None:
            candidates.append(("J", direct_j_confidence))

        model_j_confidence = self._detect_model_threshold_label("J")
        if model_j_confidence is not None:
            candidates.append(("J", model_j_confidence))

        direct_z_confidence = self._detect_direct_dynamic_label("Z", "index_shape", {"Z", "D"})
        if direct_z_confidence is not None:
            candidates.append(("Z", direct_z_confidence))

        j_confidence = self._detect_j()
        if j_confidence is not None:
            candidates.append(("J", j_confidence))

        z_confidence = self._detect_z()
        if z_confidence is not None:
            candidates.append(("Z", z_confidence))

        if not candidates:
            return None, 0.0

        prediction, confidence = max(candidates, key=lambda item: item[1])
        self.last_accepted_at = now
        self.locked_label = prediction
        self.reset(clear_lock=False)
        return prediction, confidence

    def _index_shape(self, normalized: np.ndarray) -> bool:
        index = float(np.linalg.norm(normalized[8] - normalized[5]))
        middle = float(np.linalg.norm(normalized[12] - normalized[9]))
        ring = float(np.linalg.norm(normalized[16] - normalized[13]))
        pinky = float(np.linalg.norm(normalized[20] - normalized[17]))
        return index > 0.30 and index >= max(middle, ring, pinky) * 1.05

    def _pinky_shape(self, normalized: np.ndarray) -> bool:
        middle = float(np.linalg.norm(normalized[12] - normalized[9]))
        ring = float(np.linalg.norm(normalized[16] - normalized[13]))
        pinky = float(np.linalg.norm(normalized[20] - normalized[17]))
        return pinky > 0.25 and pinky >= max(middle, ring) * 1.10

    def _recent_values(self, key: str) -> list:
        return [observation[key] for observation in self.observations]

    def _recent_observations(self, count: int) -> list:
        observations = list(self.observations)
        return observations[-count:]

    def _primary_probability_for(self, label: str) -> float:
        return float(self.primary_probabilities[label])

    def _has_model_evidence(self, label: str, fallback_labels: set[str]) -> bool:
        probabilities = self._recent_values(f"{label.lower()}_probability")
        if max(probabilities, default=0.0) >= self._primary_probability_for(label):
            return True

        observed_top_labels = set(self._recent_values("top_label"))
        return (
            bool(observed_top_labels & fallback_labels)
            and max(probabilities, default=0.0) >= self.secondary_probability
        )

    def _shape_ratio(self, key: str) -> float:
        values = self._recent_values(key)
        if not values:
            return 0.0
        return float(np.mean(values))

    def _top_ratio(self, label: str) -> float:
        top_labels_in_window = self._recent_values("top_label")
        if not top_labels_in_window:
            return 0.0
        return float(np.mean([top_label == label for top_label in top_labels_in_window]))

    def _path(self, key: str) -> np.ndarray | None:
        observations = list(self.observations)
        if len(observations) < self.min_frames:
            return None

        median_scale = float(np.median([observation["scale"] for observation in observations]))
        if median_scale < 1e-6:
            return None

        return np.asarray([observation[key] for observation in observations], dtype=np.float32) / median_scale

    def _detect_direct_dynamic_label(
        self,
        label: str,
        shape_key: str,
        supporting_top_labels: set[str],
    ) -> float | None:
        recent = self._recent_observations(self.direct_frames)
        if len(recent) < self.direct_frames:
            return None

        probability_key = f"{label.lower()}_probability"
        probabilities = [observation[probability_key] for observation in recent]
        top_ratio = float(np.mean([observation["top_label"] in supporting_top_labels for observation in recent]))
        shape_ratio = float(np.mean([observation[shape_key] for observation in recent]))

        if max(probabilities, default=0.0) < self._primary_probability_for(label):
            return None
        if top_ratio < 0.67:
            return None
        if shape_ratio < 0.50:
            return None

        return max(probabilities)

    def _detect_model_threshold_label(self, label: str) -> float | None:
        recent = self._recent_observations(self.direct_frames)
        if len(recent) < self.direct_frames:
            return None

        probability_key = f"{label.lower()}_probability"
        probabilities = [observation[probability_key] for observation in recent]
        top_ratio = float(np.mean([observation["top_label"] == label for observation in recent]))

        if max(probabilities, default=0.0) < self._primary_probability_for(label):
            return None
        if top_ratio < 0.67:
            return None

        return max(probabilities)

    def _gesture_still_active(self, label: str) -> bool:
        point_key = "pinky_tip" if label == "J" else "index_tip"
        shape_key = "pinky_shape" if label == "J" else "index_shape"
        supporting_top_labels = {"J", "I", "Y"} if label == "J" else {"Z", "D"}
        active_motion_threshold = 0.18 if label == "J" else 0.24

        if self._detect_direct_dynamic_label(label, shape_key, supporting_top_labels) is not None:
            return True

        points = self._path(point_key)
        if points is None:
            return True

        return self._shape_ratio(shape_key) >= 0.35 and path_length(points) >= active_motion_threshold

    def _detect_z(self) -> float | None:
        if not self._has_model_evidence("Z", {"Z", "D"}):
            return None
        if self._shape_ratio("index_shape") < 0.40:
            return None

        points = self._path("index_tip")
        if points is None:
            return None

        x_range = float(np.ptp(points[:, 0]))
        y_range = float(np.ptp(points[:, 1]))
        if x_range < 0.28 or y_range < 0.18 or path_length(points) < 0.65:
            return None

        if self._top_ratio("Z") >= 0.55 and path_length(points) >= 0.35 and x_range >= 0.15:
            return max(self._recent_values("z_probability"))

        first = points[0]
        one_third = points[len(points) // 3]
        two_thirds = points[(len(points) * 2) // 3]
        last = points[-1]
        dx1 = float(one_third[0] - first[0])
        dx2 = float(two_thirds[0] - one_third[0])
        dx3 = float(last[0] - two_thirds[0])
        dy2 = float(two_thirds[1] - one_third[1])

        if min(abs(dx1), abs(dx2), abs(dx3)) < 0.10:
            return None
        if np.sign(dx1) != np.sign(dx3) or np.sign(dx2) == np.sign(dx1):
            return None
        if dy2 < 0.08:
            return None

        return max(self._recent_values("z_probability"))

    def _detect_j(self) -> float | None:
        if not self._has_model_evidence("J", {"J", "I", "Y"}):
            return None
        if self._shape_ratio("pinky_shape") < 0.40:
            return None

        points = self._path("pinky_tip")
        if points is None:
            return None

        x_range = float(np.ptp(points[:, 0]))
        y_range = float(np.ptp(points[:, 1]))
        total_length = path_length(points)
        if x_range < 0.16 or y_range < 0.22 or total_length < 0.45:
            return None

        if self._top_ratio("J") >= 0.55 and total_length >= 0.25:
            return max(self._recent_values("j_probability"))

        bottom_index = int(np.argmax(points[:, 1]))
        if bottom_index < len(points) * 0.35:
            return None

        start = points[0]
        bottom = points[bottom_index]
        end = points[-1]
        if float(bottom[1] - start[1]) < 0.16:
            return None

        tail = points[bottom_index:]
        if len(tail) < 3:
            return None
        tail_x_range = float(np.ptp(tail[:, 0]))
        if tail_x_range < 0.10 and abs(float(end[0] - start[0])) < 0.14:
            return None

        return max(self._recent_values("j_probability"))


class PredictionConfirmer:
    def __init__(
        self,
        confidence_threshold: float,
        confirmation_seconds: float,
        post_accept_cooldown_seconds: float,
        hand_removed_reset_seconds: float,
        different_sign_reset_seconds: float,
    ) -> None:
        self.confidence_threshold = confidence_threshold
        self.confirmation_seconds = confirmation_seconds
        self.post_accept_cooldown_seconds = post_accept_cooldown_seconds
        self.hand_removed_reset_seconds = hand_removed_reset_seconds
        self.different_sign_reset_seconds = different_sign_reset_seconds
        self.candidate: str | None = None
        self.candidate_started_at: float | None = None
        self.last_accepted: str | None = None
        self.last_accepted_at = 0.0
        self.no_hand_started_at: float | None = None
        self.different_sign_started_at: float | None = None

    def reset_candidate(self) -> None:
        self.candidate = None
        self.candidate_started_at = None

    def reset_label(self, label: str) -> None:
        if self.candidate == label:
            self.reset_candidate()
        if self.last_accepted == label:
            self.last_accepted = None
            self.last_accepted_at = 0.0
        self.different_sign_started_at = None

    def update_no_hand(self, now: float) -> tuple[float, str]:
        self.reset_candidate()
        self.different_sign_started_at = None
        if self.no_hand_started_at is None:
            self.no_hand_started_at = now
        if now - self.no_hand_started_at >= self.hand_removed_reset_seconds:
            self.last_accepted = None
        return 0.0, "No hand"

    def update(self, prediction: str, confidence: float, now: float) -> tuple[float, str]:
        self.no_hand_started_at = None

        if confidence < self.confidence_threshold:
            self.reset_candidate()
            self.different_sign_started_at = None
            return 0.0, "Confidence below threshold"

        if prediction == self.last_accepted:
            self.reset_candidate()
            self.different_sign_started_at = None
            return 0.0, "Move hand or change sign"

        if self.last_accepted is not None and prediction != self.last_accepted:
            if self.different_sign_started_at is None:
                self.different_sign_started_at = now
            if now - self.different_sign_started_at >= self.different_sign_reset_seconds:
                self.last_accepted = None
        else:
            self.different_sign_started_at = None

        if now - self.last_accepted_at < self.post_accept_cooldown_seconds:
            self.reset_candidate()
            return 0.0, "Cooldown"

        if prediction != self.candidate:
            self.candidate = prediction
            self.candidate_started_at = now

        elapsed = now - float(self.candidate_started_at)
        progress = min(1.0, elapsed / self.confirmation_seconds)
        if elapsed >= self.confirmation_seconds:
            self.last_accepted = prediction
            self.last_accepted_at = now
            self.reset_candidate()
            return 1.0, "Accepted"

        remaining = self.confirmation_seconds - elapsed
        return progress, f"Hold {remaining:.1f}s"


class CameraSession:
    def __init__(self, settings: HandSignSettings) -> None:
        self.confirmed_text = ""
        self.confirmed_prediction: str | None = None
        self.proba_history = deque(maxlen=settings.smoothing_window)
        self.confirmer = PredictionConfirmer(
            settings.confidence_threshold,
            settings.confirmation_seconds,
            settings.post_accept_cooldown_seconds,
            settings.hand_removed_reset_seconds,
            settings.different_sign_reset_seconds,
        )
        self.dynamic_tracker = DynamicGestureTracker(
            recognition.DYNAMIC_GESTURE_WINDOW_SECONDS,
            recognition.DYNAMIC_GESTURE_MIN_FRAMES,
            recognition.DYNAMIC_GESTURE_PRIMARY_PROBABILITIES,
            recognition.DYNAMIC_GESTURE_SECONDARY_PROBABILITY,
            recognition.DYNAMIC_GESTURE_COOLDOWN_SECONDS,
            recognition.DYNAMIC_GESTURE_DIRECT_FRAMES,
        )

    def clear_histories(self) -> None:
        self.proba_history.clear()
        self.dynamic_tracker.reset()

    def prepare_frame(self) -> None:
        self.confirmed_prediction = None

    def backspace(self) -> str | None:
        if not self.confirmed_text:
            return None

        removed_letter = self.confirmed_text[-1]
        self.confirmed_text = self.confirmed_text[:-1]
        self.confirmed_prediction = None
        if removed_letter in recognition.DYNAMIC_GESTURE_LABELS:
            self.proba_history.clear()
            self.dynamic_tracker.reset_label(removed_letter)
            self.confirmer.reset_label(removed_letter)
        return removed_letter


class PredictionService:
    def __init__(self, settings: HandSignSettings) -> None:
        self.settings = settings
        self.model = self._load_model(settings.resolved_model_path(), settings.resolved_metadata_path())
        matplotlib_cache = Path("static/matplotlib_cache").resolve()
        matplotlib_cache.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("MPLCONFIGDIR", str(matplotlib_cache))
        import mediapipe as mp

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=settings.landmark_detection_confidence,
            min_tracking_confidence=settings.camera_tracking_confidence,
        )
        self._lock = threading.Lock()
        self._sessions: dict[str, CameraSession] = {}
        logger.info("Loaded sign model with classes: %s", list(self.model.classes_))

    @property
    def classes(self) -> list[str]:
        return [str(label) for label in self.model.classes_]

    def close(self) -> None:
        self.hands.close()

    def reset_session(self, session_id: str) -> None:
        self._sessions[session_id] = CameraSession(self.settings)

    def backspace_session(self, session_id: str) -> tuple[str, str | None]:
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = CameraSession(self.settings)
            session = self._sessions[session_id]
            removed_letter = session.backspace()
            return session.confirmed_text, removed_letter

    def predict_frame(self, frame: np.ndarray) -> PredictionResult:
        with self._lock:
            return self._predict(frame, session=None)

    def detect_camera_frame(self, session_id: str, frame: np.ndarray) -> tuple[PredictionResult, str, str | None, bool]:
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = CameraSession(self.settings)
            session = self._sessions[session_id]
            session.prepare_frame()
            if len(self._sessions) > self.settings.max_camera_sessions:
                oldest_key = next(iter(self._sessions))
                self._sessions.pop(oldest_key, None)

            result = self._predict(frame, session=session)
            threshold_met = result.dynamic_accepted or result.confidence >= self.settings.confidence_threshold
            return result, session.confirmed_text, session.confirmed_prediction, threshold_met

    def _predict(self, frame: np.ndarray, session: CameraSession | None) -> PredictionResult:
        height, width, _ = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(frame_rgb)

        if not result.multi_hand_landmarks:
            confirmation_progress = 0.0
            confirmation_status = "No hand"
            if session is not None:
                confirmation_progress, confirmation_status = session.confirmer.update_no_hand(time.time())
                session.clear_histories()
            return PredictionResult(
                detected=False,
                prediction=None,
                confidence=0.0,
                box=None,
                top_predictions=[],
                width=width,
                height=height,
                confirmation_progress=confirmation_progress,
                confirmation_status=confirmation_status,
            )

        hand_lm = result.multi_hand_landmarks[0]
        raw_proba, prediction_source = self._predict_probabilities_for_landmarks(hand_lm.landmark)

        if session is None:
            averaged_proba = raw_proba
        else:
            maybe_reset_history_for_new_sign(
                session.proba_history,
                raw_proba,
                self.model.classes_,
                self.settings.confidence_threshold,
            )
            session.proba_history.append(raw_proba)
            averaged_proba = weighted_average_probabilities(session.proba_history)

        pred_index = int(np.argmax(averaged_proba))
        confidence = float(averaged_proba[pred_index])
        prediction = str(self.model.classes_[pred_index])
        prediction, confidence, calibration_status = calibrate_static_problem_prediction(
            prediction,
            confidence,
            averaged_proba,
            self.model.classes_,
            hand_lm.landmark,
        )

        confirmation_progress = 0.0
        confirmation_status = "Prediction only"
        dynamic_accepted = False
        if session is not None:
            now = time.time()
            dynamic_prediction, dynamic_confidence = session.dynamic_tracker.update(
                hand_lm.landmark,
                raw_proba,
                self.model.classes_,
                now,
            )
            if dynamic_prediction is not None:
                prediction = dynamic_prediction
                confidence = dynamic_confidence
                confirmation_progress = 1.0
                confirmation_status = "Accepted motion"
                session.confirmed_text = apply_prediction(prediction, session.confirmed_text)
                session.confirmed_prediction = prediction
                session.confirmer.last_accepted = prediction
                session.confirmer.last_accepted_at = now
                session.confirmer.reset_candidate()
                session.proba_history.clear()
                dynamic_accepted = True
                logger.info("Confirmed motion %s at %.0f%% evidence", prediction, confidence * 100)
            elif (
                prediction == "J"
                and confidence >= recognition.DYNAMIC_GESTURE_PRIMARY_PROBABILITIES["J"]
                and session.confirmer.last_accepted != "J"
            ):
                confirmation_progress = 1.0
                confirmation_status = "Accepted motion"
                session.confirmed_text = apply_prediction(prediction, session.confirmed_text)
                session.confirmed_prediction = prediction
                session.confirmer.last_accepted = prediction
                session.confirmer.last_accepted_at = now
                session.confirmer.reset_candidate()
                session.dynamic_tracker.last_accepted_at = now
                session.dynamic_tracker.locked_label = prediction
                session.proba_history.clear()
                dynamic_accepted = True
                logger.info("Confirmed J at %.0f%% threshold evidence", confidence * 100)
            elif prediction in recognition.DYNAMIC_GESTURE_LABELS:
                session.confirmer.reset_candidate()
                confirmation_progress = 0.0
                confirmation_status = "Trace motion"
            else:
                confirmation_progress, confirmation_status = session.confirmer.update(prediction, confidence, now)
                if confirmation_status == "Accepted":
                    session.confirmed_text = apply_prediction(prediction, session.confirmed_text)
                    session.confirmed_prediction = prediction
                    logger.info("Confirmed %s at %.0f%%", prediction, confidence * 100)

        x_px = [int(point.x * width) for point in hand_lm.landmark]
        y_px = [int(point.y * height) for point in hand_lm.landmark]
        padding = int(max(max(x_px) - min(x_px), max(y_px) - min(y_px)) * 0.3)
        box = BoundingBox(
            x_min=max(0, min(x_px) - padding),
            x_max=min(width, max(x_px) + padding),
            y_min=max(0, min(y_px) - padding),
            y_max=min(height, max(y_px) + padding),
        )
        top_predictions = top_labels(averaged_proba, self.model.classes_)

        return PredictionResult(
            detected=True,
            prediction=prediction,
            confidence=confidence,
            box=box,
            top_predictions=top_predictions,
            width=width,
            height=height,
            prediction_source=prediction_source,
            calibration_status=calibration_status,
            confirmation_progress=confirmation_progress,
            confirmation_status=confirmation_status,
            dynamic_accepted=dynamic_accepted,
        )

    def _predict_probabilities_for_landmarks(self, landmarks) -> tuple[np.ndarray, str]:
        row = landmarks_to_feature_vector(landmarks)
        proba = self.model.predict_proba([row])[0]
        confidence = float(np.max(proba))

        if confidence >= self.settings.confidence_threshold:
            return proba, "direct"

        mirrored_row = landmarks_to_feature_vector(landmarks, mirror_x=True)
        mirrored_proba = self.model.predict_proba([mirrored_row])[0]
        mirrored_confidence = float(np.max(mirrored_proba))
        if mirrored_confidence >= confidence + recognition.MIRROR_FALLBACK_MARGIN:
            return mirrored_proba, "mirrored"

        return proba, "direct"

    def _load_model(self, model_path: Path, metadata_path: Path):
        if not model_path.exists():
            raise RuntimeError(f"Model file not found: {model_path}")

        with model_path.open("rb") as file:
            model = pickle.load(file)

        expected_features = getattr(model, "n_features_in_", None)
        if expected_features is not None and expected_features != feature_length():
            raise RuntimeError(
                f"{model_path} expects {expected_features} features, but this code produces "
                f"{feature_length()}. Re-run 2_train_model.py before using inference."
            )

        if metadata_path.exists():
            with metadata_path.open("r", encoding="utf-8") as file:
                metadata = json.load(file)
            if metadata.get("feature_version") != FEATURE_VERSION:
                raise RuntimeError(
                    f"Model feature version is {metadata.get('feature_version')}, "
                    f"but code expects {FEATURE_VERSION}. Re-run 2_train_model.py."
                )

        return model

