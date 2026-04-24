from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List

from app import models, schemas, crud
from app.core import auth
from app.db import get_db

router = APIRouter(redirect_slashes=False)

# --- PUBLIC ---

@router.get("/blog-posts", response_model=List[schemas.BlogPost])
def get_blog_posts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.BlogPost).filter(
        models.BlogPost.is_published == True,
        models.BlogPost.is_approved == True
    ).order_by(models.BlogPost.published_at.desc()).offset(skip).limit(limit).all()

@router.get("/blog-posts/admin/posts", response_model=List[schemas.BlogPost])
def get_all_posts_admin(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                        current_user: dict = Depends(auth.RoleChecker(["superuser", "editor"]))):
    return db.query(models.BlogPost).order_by(models.BlogPost.published_at.desc()).offset(skip).limit(limit).all()

@router.get("/blog-posts/{slug}", response_model=schemas.BlogPost)
def get_blog_post(slug: str, db: Session = Depends(get_db)):
    post = db.query(models.BlogPost).filter(
        models.BlogPost.slug == slug,
        models.BlogPost.is_published == True
    ).first()
    if not post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    return post

# --- ADMIN ---

@router.post("/blog-posts", response_model=schemas.BlogPost, status_code=status.HTTP_201_CREATED)
def create_blog_post(post: schemas.BlogPostCreate, db: Session = Depends(get_db),
                     current_user: dict = Depends(auth.RoleChecker(["superuser", "editor"]))):
    db_user = db.query(models.User).filter(models.User.email == current_user["email"]).first()
    is_approved = current_user["role"] == "superuser"
    try:
        db_post = models.BlogPost(**post.model_dump(), author_id=db_user.id if db_user else None, is_approved=is_approved)
        db.add(db_post)
        db.commit()
        db.refresh(db_post)
        return db_post
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="A post with this slug already exists.")

@router.post("/blog-posts/{id}/approve", response_model=schemas.BlogPost)
def approve_blog_post(id: int, db: Session = Depends(get_db),
                       current_user: dict = Depends(auth.RoleChecker(["superuser"]))):
    db_post = db.query(models.BlogPost).filter(models.BlogPost.id == id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    db_post.is_approved = True
    db.commit()
    db.refresh(db_post)
    return db_post

@router.put("/blog-posts/{id}", response_model=schemas.BlogPost)
def update_blog_post(id: int, post_update: schemas.BlogPostUpdate, db: Session = Depends(get_db),
                     current_user: dict = Depends(auth.RoleChecker(["superuser", "editor"]))):
    db_post = db.query(models.BlogPost).filter(models.BlogPost.id == id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    update_data = post_update.model_dump(exclude_unset=True)
    if "is_approved" in update_data and current_user["role"] != "superuser":
        update_data.pop("is_approved")
    for field, value in update_data.items():
        setattr(db_post, field, value)
    try:
        db.commit()
        db.refresh(db_post)
        return db_post
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="A post with this slug already exists.")

@router.delete("/blog-posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_blog_post(id: int, db: Session = Depends(get_db),
                     current_user: dict = Depends(auth.RoleChecker(["superuser", "editor"]))):
    db_post = db.query(models.BlogPost).filter(models.BlogPost.id == id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    if current_user["role"] != "superuser" and db_post.author_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    db.delete(db_post)
    db.commit()
