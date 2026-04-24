from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List

from app import models, schemas
from app.core import auth
from app.db import get_db

router = APIRouter(redirect_slashes=False)

@router.get("/admin/users", response_model=List[schemas.UserOut])
def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
              current_user: dict = Depends(auth.RoleChecker(["superuser", "editor"]))):
    return db.query(models.User).offset(skip).limit(limit).all()

@router.post("/admin/users", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db),
                current_user: dict = Depends(auth.RoleChecker(["superuser"]))):
    hashed_pw = auth.get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_pw,
                          full_name=user.full_name, role=user.role,
                          must_change_password=True)
    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="User with this email already exists.")

@router.get("/admin/users/password-requests", response_model=List[schemas.PasswordResetRequestSchema])
def get_password_requests(db: Session = Depends(get_db),
                          current_user: dict = Depends(auth.RoleChecker(["superuser"]))):
    return db.query(models.PasswordResetRequest).filter(
        models.PasswordResetRequest.status == "pending"
    ).all()

@router.post("/admin/users/password-requests/{id}/approve")
def approve_password_reset(id: int, db: Session = Depends(get_db),
                           current_user: dict = Depends(auth.RoleChecker(["superuser"]))):
    req = db.query(models.PasswordResetRequest).filter(models.PasswordResetRequest.id == id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    user = db.query(models.User).filter(models.User.id == req.user_id).first()
    if user:
        user.must_change_password = True
    req.status = "approved"
    db.commit()
    return {"message": "Approved"}

@router.post("/admin/users/password-requests/{id}/reject")
def reject_password_reset(id: int, db: Session = Depends(get_db),
                          current_user: dict = Depends(auth.RoleChecker(["superuser"]))):
    req = db.query(models.PasswordResetRequest).filter(models.PasswordResetRequest.id == id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    req.status = "rejected"
    db.commit()
    return {"message": "Rejected"}

@router.delete("/admin/users/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(id: int, db: Session = Depends(get_db),
                current_user: dict = Depends(auth.RoleChecker(["superuser"]))):
    if id == current_user["id"]:
        raise HTTPException(status_code=400, detail="You cannot delete your own account.")
    db_user = db.query(models.User).filter(models.User.id == id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
