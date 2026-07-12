import json
import logging
import pickle
import threading
import time
from collections import Counter, deque
from pathlib import Path

import cv2
import numpy as np

from core.handsign_config import HandSignSettings
from models.handsign.prediction import BoundingBox, PredictionResult
from utils.handsign.landmark_features import FEATURE_VERSION, feature_length, landmarks_to_feature_vector

logger = logging.getLogger(__name__)


class CameraSession:
    def __init__(self, smoothing_window: int, stable_frames: int) -> None:
        self.confirmed_text = ""
        self.last_confirmed_letter = ""
        self.last_confirmed_time = 0.0
        self.proba_history = deque(maxlen=smoothing_window)
        self.prediction_history = deque(maxlen=stable_frames)

    def clear_histories(self) -> None:
        self.proba_history.clear()
        self.prediction_history.clear()


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


class PredictionService:
    def __init__(self, settings: HandSignSettings) -> None:
        self.settings = settings
        self.model = self._load_model(settings.resolved_model_path(), settings.resolved_metadata_path())
        import mediapipe as mp

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
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
        self._sessions[session_id] = CameraSession(
            smoothing_window=self.settings.smoothing_window,
            stable_frames=self.settings.stable_frames,
        )

    def predict_frame(self, frame: np.ndarray) -> PredictionResult:
        with self._lock:
            return self._predict(frame, session=None)

    def detect_camera_frame(self, session_id: str, frame: np.ndarray) -> tuple[PredictionResult, str, str | None, bool]:
        with self._lock:
            session = self._sessions.setdefault(
                session_id,
                CameraSession(
                    smoothing_window=self.settings.smoothing_window,
                    stable_frames=self.settings.stable_frames,
                ),
            )
            if len(self._sessions) > self.settings.max_camera_sessions:
                oldest_key = next(iter(self._sessions))
                self._sessions.pop(oldest_key, None)
            result = self._predict(frame, session=session)
            confirmed_prediction = None
            threshold_met = False

            if result.detected and result.prediction is not None:
                threshold_met = result.confidence >= self.settings.confidence_threshold
                stable_prediction = (
                    len(session.prediction_history) == self.settings.stable_frames
                    and Counter(session.prediction_history).most_common(1)[0][1] == self.settings.stable_frames
                )
                now = time.time()
                if threshold_met and stable_prediction:
                    enough_delay = (now - session.last_confirmed_time) > self.settings.confirm_delay_seconds
                    if result.prediction != session.last_confirmed_letter or enough_delay:
                        session.confirmed_text = apply_prediction(result.prediction, session.confirmed_text)
                        session.last_confirmed_letter = result.prediction
                        session.last_confirmed_time = now
                        confirmed_prediction = result.prediction
                        logger.info("Confirmed %s at %.0f%%", result.prediction, result.confidence * 100)
            return result, session.confirmed_text, confirmed_prediction, threshold_met

    def _predict(self, frame: np.ndarray, session: CameraSession | None) -> PredictionResult:
        height, width, _ = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(frame_rgb)

        if not result.multi_hand_landmarks:
            if session is not None:
                session.clear_histories()
            return PredictionResult(
                detected=False,
                prediction=None,
                confidence=0.0,
                box=None,
                top_predictions=[],
                width=width,
                height=height,
            )

        hand_lm = result.multi_hand_landmarks[0]
        row = landmarks_to_feature_vector(hand_lm.landmark)
        raw_proba = self.model.predict_proba([row])[0]

        if session is None:
            averaged_proba = raw_proba
        else:
            session.proba_history.append(raw_proba)
            averaged_proba = weighted_average_probabilities(session.proba_history)

        pred_index = int(np.argmax(averaged_proba))
        confidence = float(averaged_proba[pred_index])
        prediction = str(self.model.classes_[pred_index])
        if session is not None:
            session.prediction_history.append(prediction)

        x_px = [int(point.x * width) for point in hand_lm.landmark]
        y_px = [int(point.y * height) for point in hand_lm.landmark]
        padding = int(max(max(x_px) - min(x_px), max(y_px) - min(y_px)) * 0.3)
        box = BoundingBox(
            x_min=max(0, min(x_px) - padding),
            x_max=min(width, max(x_px) + padding),
            y_min=max(0, min(y_px) - padding),
            y_max=min(height, max(y_px) + padding),
        )
        top_indices = np.argsort(averaged_proba)[-3:][::-1]
        top_predictions = [(str(self.model.classes_[i]), float(averaged_proba[i])) for i in top_indices]

        return PredictionResult(
            detected=True,
            prediction=prediction,
            confidence=confidence,
            box=box,
            top_predictions=top_predictions,
            width=width,
            height=height,
        )

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
