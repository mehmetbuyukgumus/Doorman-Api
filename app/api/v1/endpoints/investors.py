from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List

from app import schemas, crud
from app.core import auth
from app.db import get_db

router = APIRouter(redirect_slashes=False)

# --- INVESTORS ---

@router.get("/admin/investors", response_model=List[schemas.Investor])
def get_investors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                  current_user: dict = Depends(auth.RoleChecker(["superuser"]))):
    return crud.get_investors(db, skip=skip, limit=limit)

@router.post("/admin/investors", response_model=schemas.Investor, status_code=status.HTTP_201_CREATED)
def create_investor(investor: schemas.InvestorCreate, db: Session = Depends(get_db),
                    current_user: dict = Depends(auth.RoleChecker(["superuser"]))):
    try:
        return crud.create_investor(db=db, investor=investor)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="This email is already registered as an investor.")

@router.delete("/admin/investors/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_investor(id: int, db: Session = Depends(get_db),
                    current_user: dict = Depends(auth.RoleChecker(["superuser"]))):
    if not crud.delete_investor(db=db, investor_id=id):
        raise HTTPException(status_code=404, detail="Investor not found")

# --- BUYERS ---

@router.get("/admin/buyers", response_model=List[schemas.Buyer])
def get_buyers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
               current_user: dict = Depends(auth.RoleChecker(["superuser", "editor"]))):
    return crud.get_buyers(db, skip=skip, limit=limit)

@router.post("/admin/buyers", response_model=schemas.Buyer, status_code=status.HTTP_201_CREATED)
def create_buyer(buyer: schemas.BuyerCreate, db: Session = Depends(get_db),
                 current_user: dict = Depends(auth.RoleChecker(["superuser"]))):
    return crud.create_buyer(db=db, buyer=buyer)

@router.delete("/admin/buyers/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_buyer(id: int, db: Session = Depends(get_db),
                 current_user: dict = Depends(auth.RoleChecker(["superuser"]))):
    if not crud.delete_buyer(db=db, buyer_id=id):
        raise HTTPException(status_code=404, detail="Buyer not found")
