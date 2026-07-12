from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class HandSignSettings(BaseSettings):
    model_path: Path = Path("model/sign_model.pkl")
    metadata_path: Path = Path("model/sign_model_metadata.json")
    confidence_threshold: float = 0.80
    stable_frames: int = 4
    smoothing_window: int = 5
    confirm_delay_seconds: float = 1.5
    max_camera_sessions: int = 64

    model_config = SettingsConfigDict(env_prefix="HANDSIGN_", env_file=".env", extra="ignore")

    def resolved_model_path(self) -> Path:
        return (Path(__file__).resolve().parents[1] / self.model_path).resolve()

    def resolved_metadata_path(self) -> Path:
        return (Path(__file__).resolve().parents[1] / self.metadata_path).resolve()


@lru_cache
def get_handsign_settings() -> HandSignSettings:
    return HandSignSettings()
