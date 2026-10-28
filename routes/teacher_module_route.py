from datetime import datetime
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlalchemy.orm import Session
from limiter import limiter
from models.accounts import Accounts
from schemas.teacher_module_schema import LearningTopicOut, ModuleCheckpointCreate, ModuleCheckpointOut, TeacherModuleCreate, TeacherModuleDetailOut, TeacherModuleOut, TeacherModuleUpdate, TopicSignVideoOut
from services.module_checkpoint_service import checkpoint_summary, replace_module_checkpoints
from services.topic_sign_video_service import delete_topic_sign_video, list_topic_sign_videos, upload_topic_sign_video
from services.teacher_module_service import (
    create_teacher_module,
    create_teacher_module_upload,
    delete_teacher_module,
    download_teacher_module_file,
    get_teacher_module,
    list_teacher_modules,
    replace_teacher_module_file,
    update_teacher_module,
)
from utils.dependencies import get_db
from utils.teacher_guard import require_teacher


router = APIRouter(prefix="/teacher/modules", tags=["Teacher Modules"])


@router.get("/", response_model=list[TeacherModuleOut])
@limiter.limit("20/minute")
def list_teacher_modules_route(request: Request, db: Session = Depends(get_db), current_user: Accounts = Depends(require_teacher)):
    return list_teacher_modules(request=request, db=db, current_user=current_user)


@router.post("/", response_model=TeacherModuleOut)
@limiter.limit("10/minute")
def create_teacher_module_route(request: Request, module: TeacherModuleCreate, db: Session = Depends(get_db), current_user: Accounts = Depends(require_teacher)):
    return create_teacher_module(request=request, module=module, db=db, current_user=current_user)


@router.post("/upload", response_model=TeacherModuleOut)
@limiter.limit("10/minute")
async def create_teacher_module_upload_route(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    content_type: str = Form(...),
    week: str = Form(...),
    status_value: str = Form("Unpublished"),
    behavior_required: bool = Form(True),
    class_id: int | None = Form(None),
    due_at: datetime | None = Form(None),
    material_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(require_teacher)
):
    return await create_teacher_module_upload(
        request=request,
        title=title,
        description=description,
        content_type=content_type,
        week=week,
        status_value=status_value,
        behavior_required=behavior_required,
        class_id=class_id,
        due_at=due_at,
        material_file=material_file,
        db=db,
        current_user=current_user
    )


@router.put("/{module_id}/checkpoints", response_model=list[ModuleCheckpointOut])
@limiter.limit("10/minute")
def replace_module_checkpoints_route(
    request: Request,
    module_id: int,
    checkpoints: list[ModuleCheckpointCreate],
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(require_teacher),
):
    return replace_module_checkpoints(request, module_id, checkpoints, db, current_user)


@router.get("/{module_id}/checkpoint-summary")
@limiter.limit("20/minute")
def module_checkpoint_summary_route(
    request: Request,
    module_id: int,
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(require_teacher),
):
    return checkpoint_summary(request, module_id, db, current_user)


@router.get("/{module_id}", response_model=TeacherModuleDetailOut)
@limiter.limit("20/minute")
def get_teacher_module_route(request: Request, module_id: int, db: Session = Depends(get_db), current_user: Accounts = Depends(require_teacher)):
    return get_teacher_module(request=request, module_id=module_id, db=db, current_user=current_user)


@router.get("/{module_id}/topics", response_model=list[LearningTopicOut])
@limiter.limit("20/minute")
def get_teacher_module_topics_route(request: Request, module_id: int, db: Session = Depends(get_db), current_user: Accounts = Depends(require_teacher)):
    module = get_teacher_module(request=request, module_id=module_id, db=db, current_user=current_user)
    return sorted(module.topics, key=lambda topic: topic.sort_order)


@router.get("/{module_id}/topics/{topic_id}/sign-videos", response_model=list[TopicSignVideoOut])
@limiter.limit("20/minute")
def list_topic_sign_videos_route(request: Request, module_id: int, topic_id: int, db: Session = Depends(get_db), current_user: Accounts = Depends(require_teacher)):
    return list_topic_sign_videos(module_id, topic_id, db, current_user)


@router.post("/{module_id}/topics/{topic_id}/sign-videos", response_model=TopicSignVideoOut)
@limiter.limit("10/minute")
async def upload_topic_sign_video_route(
    request: Request,
    module_id: int,
    topic_id: int,
    focus_area: str = Form(...),
    title: str | None = Form(None),
    video: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(require_teacher),
):
    return upload_topic_sign_video(module_id, topic_id, focus_area, title, video, db, current_user)


@router.delete("/{module_id}/topics/{topic_id}/sign-videos/{sign_video_id}")
@limiter.limit("10/minute")
def delete_topic_sign_video_route(request: Request, module_id: int, topic_id: int, sign_video_id: int, db: Session = Depends(get_db), current_user: Accounts = Depends(require_teacher)):
    delete_topic_sign_video(module_id, topic_id, sign_video_id, db, current_user)
    return {"message": "Sign-language video removed."}


@router.get("/{module_id}/download")
@limiter.limit("20/minute")
def download_teacher_module_file_route(request: Request, module_id: int, db: Session = Depends(get_db), current_user: Accounts = Depends(require_teacher)):
    return download_teacher_module_file(request=request, module_id=module_id, db=db, current_user=current_user)


@router.put("/{module_id}/replace-file", response_model=TeacherModuleDetailOut)
@limiter.limit("10/minute")
async def replace_teacher_module_file_route(
    request: Request,
    module_id: int,
    material_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(require_teacher)
):
    return await replace_teacher_module_file(request=request, module_id=module_id, material_file=material_file, db=db, current_user=current_user)


@router.patch("/{module_id}", response_model=TeacherModuleOut)
@limiter.limit("10/minute")
def update_teacher_module_route(request: Request, module_id: int, update: TeacherModuleUpdate, db: Session = Depends(get_db), current_user: Accounts = Depends(require_teacher)):
    return update_teacher_module(request=request, module_id=module_id, update=update, db=db, current_user=current_user)


@router.delete("/{module_id}")
@limiter.limit("10/minute")
def delete_teacher_module_route(request: Request, module_id: int, db: Session = Depends(get_db), current_user: Accounts = Depends(require_teacher)):
    return delete_teacher_module(request=request, module_id=module_id, db=db, current_user=current_user)
