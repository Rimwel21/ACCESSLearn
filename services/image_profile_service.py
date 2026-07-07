import asyncio
from fastapi import UploadFile, HTTPException, status, Request
from sqlalchemy.orm import Session
from models.file_upload import FileUpload
from models.accounts import Accounts
from utils.storage import upload_file, delete_file
from utils.enum import FileCategory, RoleEnum
from models.student_profile import StudentProfile
from models.teacher_profile import TeacherProfile

# image upload and update
async def upload_image_profile(request: Request, image: UploadFile, db:Session, current_user: Accounts):
    if current_user.role == RoleEnum.student:
        profile = db.query(StudentProfile).filter(StudentProfile.account_id == current_user.id).first()
        
        folder="student_profiles"

    elif current_user.role == RoleEnum.teacher:
        profile = db.query(TeacherProfile).filter(TeacherProfile.account_id == current_user.id).first()

        folder="teacher_profiles"

    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
        
    profile_image = db.query(FileUpload).filter(FileUpload.owner_id == current_user.id, FileUpload.file_category == FileCategory.PROFILE_IMAGE).first()

    allowed_types = [
            "image/jpeg",
            "image/png",
            "image/webp"
        ]
    if image.content_type not in allowed_types:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only image files are allowed")
    
    file_bytes = await image.read()

    uploaded = await asyncio.to_thread(
            upload_file,
            file_bytes,
            folder
        )
    
    if not profile_image:

        new_file = FileUpload(
            filename=image.filename,
            file_type=image.content_type,
            file_url=uploaded["url"],
            public_id=uploaded["public_id"],
            file_category=FileCategory.PROFILE_IMAGE,
            owner_id=current_user.id
        )

        db.add(new_file)
        db.flush()

        # para magkaron ng id ang foreign key ng profile which is foreign sa file model
        profile.profile_image_id = new_file.id

        db.commit()
        db.refresh(profile)

        return new_file

    old_public_id = profile_image.public_id

    profile_image.filename = image.filename
    profile_image.file_type = image.content_type
    profile_image.file_url = uploaded["url"]
    profile_image.public_id = uploaded["public_id"]


    db.commit()
    db.refresh(profile_image)

    if old_public_id:
        await asyncio.to_thread(
            delete_file,
            old_public_id
        )

    return profile_image


# delete image profile
async def delete_image_profile(request: Request, db: Session, current_user: Accounts):
    if current_user.role == RoleEnum.student:
        profile = db.query(StudentProfile).filter(StudentProfile.account_id == current_user.id).first()
    elif current_user.role == RoleEnum.teacher:
        profile = db.query(TeacherProfile).filter(TeacherProfile.account_id == current_user.id).first()
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    image_profile = db.query(FileUpload).filter(FileUpload.owner_id == current_user.id, FileUpload.file_category == FileCategory.PROFILE_IMAGE).first()

    if not image_profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile image not found")
        
    await asyncio.to_thread(
        delete_file,
        image_profile.public_id
    )

    if profile:
            profile.profile_image_id = None

    db.delete(image_profile)
    db.commit()

    return {"detail": "Image successfully deleted!"}

def get_image_profile(request: Request, db: Session, current_user: Accounts):
    if current_user.role not in [RoleEnum.student, RoleEnum.teacher]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    image_profile = db.query(FileUpload).filter(
        FileUpload.owner_id == current_user.id,
        FileUpload.file_category == FileCategory.PROFILE_IMAGE
    ).first()

    if not image_profile:
        return {
            "id": None,
            "filename": "default-profile.svg",
            "file_type": "image/svg+xml",
            "file_url": "/static/default-profile.svg",
            "file_category": FileCategory.PROFILE_IMAGE,
            "is_default": True,
            "created_at": None,
            "updated_at": None,
        }

    return image_profile


