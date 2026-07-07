from pydantic import BaseModel, Field


class FrameRequest(BaseModel):
    image: str = Field(..., description="Base64 data URL or raw base64 encoded image frame.")


class CameraFrameRequest(FrameRequest):
    session_id: str = Field(..., min_length=1, max_length=100)


class ResetCameraSessionRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=100)


class BoundingBoxResponse(BaseModel):
    x_min: int
    y_min: int
    x_max: int
    y_max: int


class TopPredictionResponse(BaseModel):
    label: str
    confidence: float


class PredictionResponse(BaseModel):
    detected: bool
    prediction: str | None
    confidence: float
    box: BoundingBoxResponse | None
    top_predictions: list[TopPredictionResponse]
    frame_width: int
    frame_height: int


class CameraDetectionResponse(PredictionResponse):
    confirmed_text: str
    confirmed_prediction: str | None
    threshold_met: bool
