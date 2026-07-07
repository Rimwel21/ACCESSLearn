from models.handsign.prediction import PredictionResult
from schemas.handsign.prediction import BoundingBoxResponse, PredictionResponse, TopPredictionResponse


def to_prediction_response(result: PredictionResult) -> PredictionResponse:
    return PredictionResponse(
        detected=result.detected,
        prediction=result.prediction,
        confidence=result.confidence,
        box=BoundingBoxResponse(**result.box.__dict__) if result.box else None,
        top_predictions=[
            TopPredictionResponse(label=label, confidence=confidence)
            for label, confidence in result.top_predictions
        ],
        frame_width=result.width,
        frame_height=result.height,
    )
