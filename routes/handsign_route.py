import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from models.accounts import Accounts
from schemas.handsign.prediction import CameraDetectionResponse, CameraFrameRequest, FrameRequest, PredictionResponse, ResetCameraSessionRequest
from services.handsign.response_mapper import to_prediction_response
from utils.dependencies import get_current_user
from utils.handsign.image import decode_base64_image

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/handsign", tags=["Hand Sign Language"])


@router.get("/health")
def health(request: Request, current_user: Accounts = Depends(get_current_user)) -> dict[str, object]:
    service = request.app.state.handsign_prediction_service
    return {
        "status": "ok",
        "classes": service.classes,
        "user_role": current_user.role,
    }


@router.post("/predict", response_model=PredictionResponse)
def predict(
    request: Request,
    payload: FrameRequest,
    current_user: Accounts = Depends(get_current_user),
) -> PredictionResponse:
    try:
        frame = decode_base64_image(payload.image)
        result = request.app.state.handsign_prediction_service.predict_frame(frame)
        return to_prediction_response(result)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Hand sign prediction failed for account %s", current_user.id)
        raise HTTPException(status_code=500, detail="Prediction failed.") from exc


@router.post("/detect", response_model=CameraDetectionResponse)
def detect_camera_frame(
    request: Request,
    payload: CameraFrameRequest,
    current_user: Accounts = Depends(get_current_user),
) -> CameraDetectionResponse:
    try:
        frame = decode_base64_image(payload.image)
        result, confirmed_text, confirmed_prediction, threshold_met = (
            request.app.state.handsign_prediction_service.detect_camera_frame(payload.session_id, frame)
        )
        prediction = to_prediction_response(result)
        return CameraDetectionResponse(
            **prediction.model_dump(),
            confirmed_text=confirmed_text,
            confirmed_prediction=confirmed_prediction,
            threshold_met=threshold_met,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Hand sign camera detection failed for account %s", current_user.id)
        raise HTTPException(status_code=500, detail="Camera detection failed.") from exc


@router.post("/reset")
def reset_camera_session(
    request: Request,
    payload: ResetCameraSessionRequest,
    current_user: Accounts = Depends(get_current_user),
) -> dict[str, str]:
    request.app.state.handsign_prediction_service.reset_session(payload.session_id)
    logger.info("Reset hand sign camera session for account %s", current_user.id)
    return {"status": "reset"}
