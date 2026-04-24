from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
import cloudinary.uploader
from typing import List

from app.core import auth

router = APIRouter(redirect_slashes=False)

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

@router.delete("/upload-image/{public_id}")
async def delete_image(
    public_id: str,
    current_user: dict = Depends(auth.RoleChecker(["superuser", "editor"]))
):
    try:
        # public_id might contain slashes if using folders
        cloudinary.uploader.destroy(public_id)
        return {"message": "Image deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image deletion failed: {str(e)}")
