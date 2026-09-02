from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from core import handsign_recognition as recognition


class HandSignSettings(BaseSettings):
    model_path: Path = Path("model/sign_model.pkl")
    metadata_path: Path = Path("model/sign_model_metadata.json")
    word_gesture_model_path: Path = Path("model/word_gesture_model.pkl")
    word_gesture_metadata_path: Path = Path("model/word_gesture_metadata.json")
    word_gesture_dataset_path: Path = Path("model/word_gestures")
    tutorial_assets_path: Path = Path("static/handsign/tutorial_assets")
    word_sequence_length: int = 40
    tutorial_attempt_count: int = 3
    confidence_threshold: float = recognition.CONFIDENCE_THRESHOLD
    smoothing_window: int = recognition.SMOOTHING_WINDOW
    landmark_detection_confidence: float = recognition.LANDMARK_DETECTION_CONFIDENCE
    camera_tracking_confidence: float = recognition.CAMERA_TRACKING_CONFIDENCE
    confirmation_seconds: float = recognition.CONFIRMATION_SECONDS
    post_accept_cooldown_seconds: float = recognition.POST_ACCEPT_COOLDOWN_SECONDS
    hand_removed_reset_seconds: float = recognition.HAND_REMOVED_RESET_SECONDS
    different_sign_reset_seconds: float = recognition.DIFFERENT_SIGN_RESET_SECONDS
    max_camera_sessions: int = 64

    model_config = SettingsConfigDict(env_prefix="HANDSIGN_", env_file=".env", extra="ignore")

    def _resolve_backend_path(self, path: Path) -> Path:
        if path.is_absolute():
            return path.resolve()
        return (Path(__file__).resolve().parents[1] / path).resolve()

    def resolved_model_base_path(self) -> Path:
        return self.resolved_model_path().parent

    def resolved_model_path(self) -> Path:
        return self._resolve_backend_path(self.model_path)

    def resolved_metadata_path(self) -> Path:
        return self._resolve_backend_path(self.metadata_path)

    def resolved_word_gesture_model_path(self) -> Path:
        return self._resolve_backend_path(self.word_gesture_model_path)

    def resolved_word_gesture_metadata_path(self) -> Path:
        return self._resolve_backend_path(self.word_gesture_metadata_path)

    def resolved_word_gesture_dataset_path(self) -> Path:
        return self._resolve_backend_path(self.word_gesture_dataset_path)

    def resolved_tutorial_assets_path(self) -> Path:
        return self._resolve_backend_path(self.tutorial_assets_path)


@lru_cache
def get_handsign_settings() -> HandSignSettings:
    return HandSignSettings()
