from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List

from app import schemas, crud
from app.core import auth
from app.db import get_db

router = APIRouter()

# --- Investor Endpoints ---

@router.get("/", response_model=List[schemas.Investor])
def read_investors(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.RoleChecker(["superuser"]))
):
    return crud.get_investors(db, skip=skip, limit=limit)

@router.post("/", response_model=schemas.Investor, status_code=status.HTTP_201_CREATED)
def create_investor(
    investor: schemas.InvestorCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.RoleChecker(["superuser"]))
):
    try:
        return crud.create_investor(db=db, investor=investor)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="This email is already registered as an investor.")

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_investor(
    id: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.RoleChecker(["superuser"]))
):
    success = crud.delete_investor(db=db, investor_id=id)
    if not success:
        raise HTTPException(status_code=404, detail="Investor not found")
    return None

# --- Buyer Endpoints ---

@router.get("/buyers", response_model=List[schemas.Buyer])
def read_buyers(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.RoleChecker(["superuser", "editor"]))
):
    return crud.get_buyers(db, skip=skip, limit=limit)

@router.post("/buyers", response_model=schemas.Buyer, status_code=status.HTTP_201_CREATED)
def create_buyer(
    buyer: schemas.BuyerCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.RoleChecker(["superuser"]))
):
    return crud.create_buyer(db=db, buyer=buyer)

@router.delete("/buyers/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_buyer(
    id: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.RoleChecker(["superuser"]))
):
    success = crud.delete_buyer(db=db, buyer_id=id)
    if not success:
        raise HTTPException(status_code=404, detail="Buyer not found")
    return None
