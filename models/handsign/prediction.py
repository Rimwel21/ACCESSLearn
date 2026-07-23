from dataclasses import dataclass


@dataclass(frozen=True)
class BoundingBox:
    x_min: int
    y_min: int
    x_max: int
    y_max: int


@dataclass(frozen=True)
class PredictionResult:
    detected: bool
    prediction: str | None
    confidence: float
    box: BoundingBox | None
    top_predictions: list[tuple[str, float]]
    width: int
    height: int
    prediction_source: str = "direct"
    calibration_status: str | None = None
    confirmation_progress: float = 0.0
    confirmation_status: str = "No hand"
    dynamic_accepted: bool = False
