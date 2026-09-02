import logging

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from models.accounts import Accounts
from schemas.handsign.prediction import (
    BackspaceCameraSessionResponse,
    CameraDetectionResponse,
    CameraFrameRequest,
    FrameRequest,
    PredictionResponse,
    ResetCameraSessionRequest,
)
from schemas.handsign.tutorial import (
    FrameSequenceScoreRequest,
    PracticeResultCreate,
    PracticeResultOut,
    SequenceScoreRequest,
    SequenceScoreResponse,
    TutorialStatus,
)
from services.handsign.response_mapper import to_prediction_response
from services.handsign.tutorial_service import save_practice_result, save_tutorial_video, tutorial_status
from services.handsign.word_frame_scoring_service import score_frame_sequence
from services.handsign.word_gesture_service import word_gesture_summary
from services.handsign.word_scoring_service import score_sequence
from utils.dependencies import get_current_user, get_db
from utils.enum import RoleEnum
from utils.handsign.image import decode_base64_image

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/handsign", tags=["Hand Sign Language"])


def _prediction_service(request: Request):
    service = getattr(request.app.state, "handsign_prediction_service", None)
    if service is None:
        raise HTTPException(status_code=503, detail="Hand sign alphabet model is not loaded.")
    return service


@router.get("/health")
def health(request: Request, current_user: Accounts = Depends(get_current_user)) -> dict[str, object]:
    service = getattr(request.app.state, "handsign_prediction_service", None)
    return {
        "status": "ok" if service is not None else "model_unavailable",
        "classes": service.classes if service is not None else [],
        "user_role": current_user.role,
        "word_gestures": word_gesture_summary(),
    }


@router.post("/predict", response_model=PredictionResponse)
def predict(
    request: Request,
    payload: FrameRequest,
    current_user: Accounts = Depends(get_current_user),
) -> PredictionResponse:
    try:
        frame = decode_base64_image(payload.image)
        result = _prediction_service(request).predict_frame(frame)
        return to_prediction_response(result)
    except HTTPException:
        raise
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
            _prediction_service(request).detect_camera_frame(payload.session_id, frame)
        )
        prediction = to_prediction_response(result)
        return CameraDetectionResponse(
            **prediction.model_dump(),
            confirmed_text=confirmed_text,
            confirmed_prediction=confirmed_prediction,
            threshold_met=threshold_met,
            confirmation_progress=result.confirmation_progress,
            confirmation_status=result.confirmation_status,
            dynamic_accepted=result.dynamic_accepted,
        )
    except HTTPException:
        raise
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
    _prediction_service(request).reset_session(payload.session_id)
    logger.info("Reset hand sign camera session for account %s", current_user.id)
    return {"status": "reset"}


@router.post("/backspace", response_model=BackspaceCameraSessionResponse)
def backspace_camera_session(
    request: Request,
    payload: ResetCameraSessionRequest,
    current_user: Accounts = Depends(get_current_user),
) -> BackspaceCameraSessionResponse:
    confirmed_text, removed_letter = _prediction_service(request).backspace_session(payload.session_id)
    logger.info("Backspaced hand sign camera session for account %s", current_user.id)
    return BackspaceCameraSessionResponse(confirmed_text=confirmed_text, removed_letter=removed_letter)


@router.get("/word-gestures/summary")
def word_gestures_summary(current_user: Accounts = Depends(get_current_user)) -> dict:
    logger.debug("Word gesture summary requested by account %s", current_user.id)
    return word_gesture_summary()


@router.get("/tutorials/{word}", response_model=TutorialStatus)
def get_tutorial_status(word: str, current_user: Accounts = Depends(get_current_user)) -> TutorialStatus:
    logger.debug("Tutorial status for %s requested by account %s", word, current_user.id)
    return TutorialStatus(**tutorial_status(word))

@router.post("/tutorials/{word}/video", response_model=TutorialStatus)
async def upload_tutorial_video(
    word: str,
    video: UploadFile = File(...),
    current_user: Accounts = Depends(get_current_user),
) -> TutorialStatus:
    if current_user.role != RoleEnum.teacher:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher only")
    try:
        status_payload = await save_tutorial_video(word, video)
        logger.info("Tutorial video for %s uploaded by teacher account %s", status_payload["word"], current_user.id)
        return TutorialStatus(**status_payload)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@router.post("/tutorials/practice/score", response_model=SequenceScoreResponse)
def score_tutorial_sequence(
    payload: SequenceScoreRequest,
    current_user: Accounts = Depends(get_current_user),
) -> SequenceScoreResponse:
    try:
        logger.debug("Tutorial raw sequence score requested by account %s", current_user.id)
        return SequenceScoreResponse(**score_sequence(payload.word, payload.sequence))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/tutorials/practice/score-frames", response_model=SequenceScoreResponse)
def score_tutorial_frame_sequence(
    payload: FrameSequenceScoreRequest,
    current_user: Accounts = Depends(get_current_user),
) -> SequenceScoreResponse:
    try:
        logger.debug("Tutorial frame sequence score requested by account %s", current_user.id)
        return SequenceScoreResponse(**score_frame_sequence(payload.word, payload.images))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/tutorials/practice/results", response_model=PracticeResultOut)
def save_tutorial_practice_result(
    payload: PracticeResultCreate,
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user),
) -> PracticeResultOut:
    try:
        record = save_practice_result(
            activity_id=payload.activity_id,
            word=payload.word,
            attempt_scores=payload.attempt_scores,
            db=db,
            current_user=current_user,
        )
        return PracticeResultOut(
            id=record.id,
            activity_id=record.activity_id,
            student_id=record.student_id,
            progress_id=record.progress_id,
            word=record.canonical_word,
            attempt_scores=record.attempt_scores or [],
            highest_score=record.highest_score,
            completed_at=record.completed_at,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
