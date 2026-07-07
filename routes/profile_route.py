from fastapi import APIRouter, Depends, UploadFile,File, Request
from sqlalchemy.orm import Session
from utils.dependencies import get_db, get_current_user
from services.student_profile_service import create_student_profile, get_student_profile, update_student_profile
from services.teacher_profile_service import create_teacher_profile, get_teacher_profile, update_teacher_profile
from models.accounts import Accounts
from schemas.student_profile_schema import StudentProfileCreate, StudentProfileOut, StudentProfileUpdate
from schemas.teacher_profile_schema import TeacherProfileCreate, TeacherProfileOut, TeacherProfileUpdate
from schemas.file_schema import FileOut, ProfileImageOut
from services.image_profile_service import upload_image_profile, delete_image_profile, get_image_profile
from limiter import limiter

router = APIRouter(prefix="/profile", tags=["Profiling"])

# router for GET profile and image profile
@router.get("/student/get_profile", response_model=StudentProfileOut)
@limiter.limit("20/minute")
def get_student_profile_route(request: Request, db: Session = Depends(get_db), current_user: Accounts = Depends(get_current_user)):
    return get_student_profile(
        request=request,
        db=db,
        current_user=current_user
    )

@router.get("/teacher/get_profile", response_model=TeacherProfileOut)
@limiter.limit("20/minute")
def get_teacher_profile_route(request: Request, db: Session = Depends(get_db), current_user: Accounts = Depends(get_current_user)):
    return get_teacher_profile(
        request=request,
        db=db,
        current_user=current_user
    )

@router.get("/image/get_image", response_model=ProfileImageOut)
@limiter.limit("20/minute")
def get_image_profile_route(request: Request, db: Session = Depends(get_db), current_user: Accounts = Depends(get_current_user)):
    return get_image_profile(
        request=request,
        db=db,
        current_user=current_user
    )


# route for image upload profile
@router.put("/image/upload", response_model=FileOut)
@limiter.limit("5/minute")
async def upload_image_profile_route(request: Request, image: UploadFile = File(...), db: Session = Depends(get_db), current_user: Accounts = Depends(get_current_user)):

    return await upload_image_profile(
        request=request,
        image=image,
        db=db,
        current_user=current_user
    )

# student profile setup
@router.post("/student/create", response_model=StudentProfileOut)
@limiter.limit("5/minute")
def create_student_profile_route(request:Request, student: StudentProfileCreate, db: Session = Depends(get_db), current_user: Accounts = Depends(get_current_user)):
    return create_student_profile(
        request=request,
        student=student,
        db=db,
        current_user=current_user
    )

# update student profile
@router.patch("/student/update", response_model=StudentProfileOut)
@limiter.limit("5/minute")
def update_student_profile_route(request: Request, update: StudentProfileUpdate, db: Session = Depends(get_db), current_user: Accounts = Depends(get_current_user)):
    return update_student_profile(
        request=request,
        update=update,
        db=db,
        current_user=current_user
    )

# teacher profile setup
@router.post("/teacher/create", response_model=TeacherProfileOut)
@limiter.limit("5/minute")
def create_teacher_profile_route(request: Request, teacher: TeacherProfileCreate, db: Session = Depends(get_db), current_user: Accounts = Depends(get_current_user)):
    return create_teacher_profile(
        request=request,
        teacher=teacher,
        db=db,
        current_user=current_user
    )

@router.patch("/teacher/update", response_model=TeacherProfileOut)
@limiter.limit("5/minute")
def update_teacher_profile_route(request: Request, update: TeacherProfileUpdate, db: Session = Depends(get_db), current_user: Accounts = Depends(get_current_user)):
    return update_teacher_profile(
        request=request,
        update=update,
        db=db,
        current_user=current_user
    )


# image deletion
@router.delete("/image/delete")
@limiter.limit("5/minute")
async def delete_image_profile_route(request: Request, db: Session = Depends(get_db), current_user: Accounts = Depends(get_current_user)):
    return await delete_image_profile(
        request=request,
        db=db,
        current_user=current_user
    )

