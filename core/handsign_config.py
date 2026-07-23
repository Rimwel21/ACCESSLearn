from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from core import handsign_recognition as recognition


class HandSignSettings(BaseSettings):
    model_path: Path = Path("model/sign_model.pkl")
    metadata_path: Path = Path("model/sign_model_metadata.json")
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

    def resolved_model_path(self) -> Path:
        return (Path(__file__).resolve().parents[1] / self.model_path).resolve()

    def resolved_metadata_path(self) -> Path:
        return (Path(__file__).resolve().parents[1] / self.metadata_path).resolve()


@lru_cache
def get_handsign_settings() -> HandSignSettings:
    return HandSignSettings()
