from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel

from app import models, schemas
from app.core import auth
from app.db import get_db

router = APIRouter(redirect_slashes=False)

class ForgotPasswordRequest(BaseModel):
    email: str

@router.post("/login", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email, "role": user.role, "id": user.id}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer", "must_change_password": user.must_change_password}

@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def request_password_reset(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == req.email).first()
    if user:
        reset_req = models.PasswordResetRequest(user_id=user.id, status="pending")
        db.add(reset_req)
        db.commit()
    return {"message": "Reset request submitted"}

@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(req: schemas.ResetPasswordRequest, db: Session = Depends(get_db)):
    auth_req = db.query(models.PasswordReset).filter(models.PasswordReset.token == req.token).first()
    if not auth_req:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    user = db.query(models.User).filter(models.User.email == auth_req.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.hashed_password = auth.get_password_hash(req.new_password)
    db.delete(auth_req)
    db.commit()
    return {"message": "Password reset successfully"}

@router.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(payload: schemas.PasswordChange, db: Session = Depends(get_db), current_user: dict = Depends(auth.get_current_user)):
    user = db.query(models.User).filter(models.User.email == current_user["email"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.must_change_password:
        if not payload.old_password or not auth.verify_password(payload.old_password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect current password")
    
    user.hashed_password = auth.get_password_hash(payload.new_password)
    user.must_change_password = False
    db.commit()
    return {"message": "Password updated successfully"}
