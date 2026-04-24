from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app import models, schemas
from app.core import auth
from app.db import get_db

# Combined router for all message related endpoints
router = APIRouter(redirect_slashes=False)

# --- PUBLIC ---

@router.post("/contact", response_model=schemas.ContactMessage, status_code=status.HTTP_201_CREATED)
def create_contact_message(message: schemas.ContactRequest, db: Session = Depends(get_db)):
    db_message = models.ContactMessage(**message.model_dump())
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

# --- ADMIN ---

@router.get("/admin/contact-messages", response_model=List[schemas.ContactMessage])
def get_contact_messages(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                          current_user: dict = Depends(auth.RoleChecker(["superuser", "editor"]))):
    return db.query(models.ContactMessage).order_by(
        models.ContactMessage.created_at.desc()
    ).offset(skip).limit(limit).all()

@router.patch("/admin/contact-messages/{id}", response_model=schemas.ContactMessage)
def update_contact_message(id: int, update: schemas.ContactMessageUpdate, db: Session = Depends(get_db),
                            current_user: dict = Depends(auth.RoleChecker(["superuser", "editor"]))):
    msg = db.query(models.ContactMessage).filter(models.ContactMessage.id == id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(msg, field, value)
    db.commit()
    db.refresh(msg)
    return msg

@router.delete("/admin/contact-messages/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact_message(id: int, db: Session = Depends(get_db),
                            current_user: dict = Depends(auth.RoleChecker(["superuser"]))):
    msg = db.query(models.ContactMessage).filter(models.ContactMessage.id == id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    db.delete(msg)
    db.commit()
