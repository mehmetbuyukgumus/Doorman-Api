from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional

from app import models, schemas, crud
from app.core import auth
from app.db import get_db
from app.services import mail as mail_service

router = APIRouter()

# --- Public Endpoints ---

@router.get("/properties", response_model=List[schemas.Listing])
def get_properties(
    skip: int = 0, 
    limit: int = 100, 
    listing_type: Optional[str] = None,
    location: Optional[str] = None,
    property_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    rooms: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return crud.get_listings(
        db, 
        skip=skip, 
        limit=limit,
        listing_type=listing_type,
        location=location,
        property_type=property_type,
        min_price=min_price,
        max_price=max_price,
        rooms=rooms
    )

@router.get("/listings/filters")
def get_listing_filters(db: Session = Depends(get_db)):
    neighborhoods = db.query(models.PropertyDetails.neighborhood).distinct().filter(models.PropertyDetails.neighborhood != None).all()
    types = db.query(models.PropertyDetails.property_type).distinct().filter(models.PropertyDetails.property_type != None).all()
    
    return {
        "neighborhoods": [n[0] for n in neighborhoods],
        "types": [t[0] for t in types]
    }

@router.get("/properties/{id}", response_model=schemas.Listing)
def get_property(id: int, db: Session = Depends(get_db)):
    property = db.query(models.Listing).filter(models.Listing.id == id).first()
    if property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    return property

# --- Protected Listing Endpoints ---

@router.post("/properties/", response_model=schemas.Listing, status_code=status.HTTP_201_CREATED)
def create_property(
    listing: schemas.ListingCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.RoleChecker(["superuser", "editor"]))
):
    db_user = db.query(models.User).filter(models.User.email == current_user["email"]).first()
    user_id = db_user.id if db_user else None
    return crud.create_listing(db=db, listing=listing, user_id=user_id)

@router.put("/properties/{id}", response_model=schemas.Listing)
def update_property(
    id: int,
    listing: schemas.ListingUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.RoleChecker(["superuser", "editor"]))
):
    db_user = db.query(models.User).filter(models.User.email == current_user["email"]).first()
    user_id = db_user.id if db_user else None
    updated_listing = crud.update_listing(db=db, listing_id=id, listing_update=listing, user_id=user_id)
    if not updated_listing:
        raise HTTPException(status_code=404, detail="Property not found")
    return updated_listing

@router.delete("/properties/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_property(
    id: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.RoleChecker(["superuser"]))
):
    success = crud.delete_listing(db=db, listing_id=id)
    if not success:
        raise HTTPException(status_code=404, detail="Property not found")
    return None

# --- Research Listing Endpoints ---

@router.get("/admin/research-listings", response_model=List[schemas.ResearchListing])
def read_research_listings(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.RoleChecker(["superuser", "editor"]))
):
    return crud.get_research_listings(db, skip=skip, limit=limit)

@router.post("/admin/research-listings", response_model=schemas.ResearchListing, status_code=status.HTTP_201_CREATED)
def create_research_listing(
    listing: schemas.ResearchListingCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.RoleChecker(["superuser", "editor"]))
):
    try:
        return crud.create_research_listing(db=db, listing=listing, user_id=current_user["id"])
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="This URL has already been added to the research list.")

@router.put("/admin/research-listings{id}", response_model=schemas.ResearchListing)
def update_research_listing(
    id: int,
    updates: schemas.ResearchListingUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.RoleChecker(["superuser", "editor"]))
):
    try:
        listing = crud.update_research_listing(db=db, listing_id=id, updates=updates)
        if not listing:
            raise HTTPException(status_code=404, detail="Research listing not found")
        return listing
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="This URL is already assigned to another research listing.")

@router.delete("/admin/research-listings{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_research_listing(
    id: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.RoleChecker(["superuser"]))
):
    success = crud.delete_research_listing(db=db, listing_id=id)
    if not success:
        raise HTTPException(status_code=404, detail="Research listing not found")
    return None

@router.post("/admin/research-listings/send-mail")
async def send_research_mail(
    payload: schemas.SendResearchMailRequest, 
    db: Session = Depends(get_db), 
    current_user: dict = Depends(auth.RoleChecker(["superuser"]))
):
    listing = db.query(models.ResearchListing).filter(models.ResearchListing.id == payload.listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    if payload.investor_ids and len(payload.investor_ids) > 0:
        investors = db.query(models.Investor).filter(models.Investor.id.in_(payload.investor_ids)).all()
    else:
        investors = db.query(models.Investor).all()
        
    if not investors:
        raise HTTPException(status_code=400, detail="No matching investors found")
    
    success_count = await mail_service.send_research_listing_to_investors(
        investors=investors,
        listing=listing,
        image_url=payload.image_url,
        additional_message=payload.additional_message
    )
    
    return {"message": f"Successfully sent mail to {success_count} investors"}

# --- Research Tag Endpoints ---

@router.get("/admin/research-tags", response_model=List[schemas.ResearchTag])
def read_research_tags(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.RoleChecker(["superuser", "editor"]))
):
    return crud.get_research_tags(db)

@router.post("/admin/research-tags", response_model=schemas.ResearchTag)
def create_research_tag(
    tag: schemas.ResearchTagCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.RoleChecker(["superuser", "editor"]))
):
    try:
        return crud.create_research_tag(db, tag)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Tag already exists.")

@router.delete("/admin/research-tags/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_research_tag(
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.RoleChecker(["superuser", "editor"]))
):
    success = crud.delete_research_tag(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Tag not found")
    return None
