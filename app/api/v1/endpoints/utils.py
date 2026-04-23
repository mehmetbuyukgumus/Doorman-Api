from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import cloudinary.uploader
from typing import List

from app.core import auth

router = APIRouter()

@router.post("/upload-images")
async def upload_images(
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(auth.RoleChecker(["superuser", "editor"]))
):
    results = []
    for file in files:
        try:
            upload_result = cloudinary.uploader.upload(file.file)
            results.append({
                "url": upload_result.get("secure_url"),
                "public_id": upload_result.get("public_id")
            })
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")
    return results

@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(auth.RoleChecker(["superuser", "editor"]))
):
    try:
        upload_result = cloudinary.uploader.upload(file.file)
        return {
            "url": upload_result.get("secure_url"),
            "public_id": upload_result.get("public_id")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")
