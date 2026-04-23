from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List

from app import models, schemas
from app.core import auth
from app.db import get_db

router = APIRouter()

@router.get("" , response_model=List[schemas.UserSchema])
def read_admin_users(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.RoleChecker(["superuser"]))
):
    return db.query(models.User).all()

@router.post("" , response_model=schemas.UserSchema, status_code=status.HTTP_201_CREATED)
def create_admin_user(
    user: schemas.UserCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.RoleChecker(["superuser"]))
):
    # Default password for new users is their email
    hashed_pw = auth.get_password_hash(user.email)
    db_user = models.User(
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        hashed_password=hashed_pw,
        is_active=True,
        must_change_password=True
    )
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="User with this email already exists.")

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin_user(
    id: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.RoleChecker(["superuser"]))
):
    # Cannot delete self
    if id == current_user["id"]:
        raise HTTPException(status_code=400, detail="You cannot delete your own account.")
        
    db_user = db.query(models.User).filter(models.User.id == id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    db.delete(db_user)
    db.commit()
    return None

@router.get("/password-requests", response_model=List[schemas.PasswordResetRequestSchema])
def read_password_reset_requests(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.RoleChecker(["superuser"]))
):
    return db.query(models.PasswordResetRequest).filter(models.PasswordResetRequest.status == "pending").all()

@router.post("/password-requests/{id}/approve")
def approve_password_reset(
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.RoleChecker(["superuser"]))
):
    req = db.query(models.PasswordResetRequest).filter(models.PasswordResetRequest.id == id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    
    user = db.query(models.User).filter(models.User.id == req.user_id).first()
    if user:
        # Reset password to email and force change
        user.hashed_password = auth.get_password_hash(user.email)
        user.must_change_password = True
    
    req.status = "approved"
    db.commit()
    return {"message": "Password reset approved"}

@router.post("/password-requests/{id}/reject")
def reject_password_reset(
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.RoleChecker(["superuser"]))
):
    req = db.query(models.PasswordResetRequest).filter(models.PasswordResetRequest.id == id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    
    req.status = "rejected"
    db.commit()
    return {"message": "Password reset rejected"}
