from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional

from . import models, schemas

# --- Listing CRUD ---

def get_listings(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    listing_type: Optional[str] = None,
    location: Optional[str] = None,
    property_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    rooms: Optional[str] = None
):
    query = db.query(models.Listing)
    
    if listing_type:
        query = query.filter(models.Listing.listing_type == listing_type)
    
    if location:
        query = query.join(models.PropertyDetails).filter(
            or_(
                models.PropertyDetails.neighborhood.ilike(f"%{location}%"),
                models.PropertyDetails.address.ilike(f"%{location}%")
            )
        )
    
    if property_type:
        if not location:
            query = query.join(models.PropertyDetails)
        query = query.filter(models.PropertyDetails.property_type == property_type)
        
    if min_price is not None:
        query = query.filter(models.Listing.price >= min_price)
    
    if max_price is not None:
        query = query.filter(models.Listing.price <= max_price)
        
    if rooms:
        if not (location or property_type):
            query = query.join(models.PropertyDetails)
        if rooms == "4+":
            query = query.filter(models.PropertyDetails.bedrooms >= 4)
        else:
            query = query.filter(models.PropertyDetails.bedrooms == int(rooms))

    return query.order_by(models.Listing.created_at.desc()).offset(skip).limit(limit).all()

def create_listing(db: Session, listing: schemas.ListingCreate, user_id: int):
    db_listing = models.Listing(
        title=listing.title,
        price=listing.price,
        listing_type=listing.listing_type,
        status=listing.status,
        created_by_id=user_id,
        updated_by_id=user_id
    )
    db.add(db_listing)
    db.commit()
    db.refresh(db_listing)

    db_details = models.PropertyDetails(
        **listing.details.model_dump(),
        listing_id=db_listing.id
    )
    db.add(db_details)
    
    for media_item in listing.media:
        db_media = models.Media(
            **media_item.model_dump(),
            listing_id=db_listing.id
        )
        db.add(db_media)
    
    db.commit()
    db.refresh(db_listing)
    return db_listing

def update_listing(db: Session, listing_id: int, listing_update: schemas.ListingUpdate, user_id: int):
    db_listing = db.query(models.Listing).filter(models.Listing.id == listing_id).first()
    if not db_listing:
        return None
    
    # Update main listing fields
    update_data = listing_update.model_dump(exclude_unset=True)
    if 'details' in update_data:
        details_data = update_data.pop('details')
        db_details = db.query(models.PropertyDetails).filter(models.PropertyDetails.listing_id == listing_id).first()
        if db_details:
            for key, value in details_data.items():
                setattr(db_details, key, value)
    
    if 'media' in update_data:
        media_data = update_data.pop('media')
        # Simple approach: remove all and re-add
        db.query(models.Media).filter(models.Media.listing_id == listing_id).delete()
        for media_item in media_data:
            db_media = models.Media(**media_item, listing_id=listing_id)
            db.add(db_media)

    for key, value in update_data.items():
        setattr(db_listing, key, value)
    
    db_listing.updated_by_id = user_id
    db.commit()
    db.refresh(db_listing)
    return db_listing

def delete_listing(db: Session, listing_id: int):
    db_listing = db.query(models.Listing).filter(models.Listing.id == listing_id).first()
    if db_listing:
        db.delete(db_listing)
        db.commit()
        return True
    return False

# --- Research Listing CRUD ---

def get_research_listings(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.ResearchListing).order_by(models.ResearchListing.created_at.desc()).offset(skip).limit(limit).all()

def create_research_listing(db: Session, listing: schemas.ResearchListingCreate, user_id: int):
    tag_ids = listing.tag_ids
    listing_data = listing.model_dump(exclude={"tag_ids"})
    
    db_listing = models.ResearchListing(**listing_data, created_by_id=user_id)
    
    if tag_ids:
        tags = db.query(models.ResearchTag).filter(models.ResearchTag.id.in_(tag_ids)).all()
        db_listing.tags = tags
        
    db.add(db_listing)
    db.commit()
    db.refresh(db_listing)
    return db_listing

def update_research_listing(db: Session, listing_id: int, updates: schemas.ResearchListingUpdate):
    db_listing = db.query(models.ResearchListing).filter(models.ResearchListing.id == listing_id).first()
    if not db_listing:
        return None
        
    update_data = updates.model_dump(exclude_unset=True)
    
    if "tag_ids" in update_data:
        tag_ids = update_data.pop("tag_ids")
        tags = db.query(models.ResearchTag).filter(models.ResearchTag.id.in_(tag_ids)).all()
        db_listing.tags = tags
        
    for key, value in update_data.items():
        setattr(db_listing, key, value)
        
    db.commit()
    db.refresh(db_listing)
    return db_listing

def delete_research_listing(db: Session, listing_id: int):
    db_listing = db.query(models.ResearchListing).filter(models.ResearchListing.id == listing_id).first()
    if db_listing:
        db.delete(db_listing)
        db.commit()
        return True
    return False

# --- Research Tag CRUD ---

def get_research_tags(db: Session):
    return db.query(models.ResearchTag).all()

def create_research_tag(db: Session, tag: schemas.ResearchTagCreate):
    db_tag = models.ResearchTag(name=tag.name)
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag

def delete_research_tag(db: Session, tag_id: int):
    db_tag = db.query(models.ResearchTag).filter(models.ResearchTag.id == tag_id).first()
    if db_tag:
        db.delete(db_tag)
        db.commit()
        return True
    return False

# --- Investor CRUD ---

def get_investors(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Investor).offset(skip).limit(limit).all()

def create_investor(db: Session, investor: schemas.InvestorCreate):
    db_investor = models.Investor(**investor.model_dump())
    db.add(db_investor)
    db.commit()
    db.refresh(db_investor)
    return db_investor

def delete_investor(db: Session, investor_id: int):
    db_investor = db.query(models.Investor).filter(models.Investor.id == investor_id).first()
    if db_investor:
        db.delete(db_investor)
        db.commit()
        return True
    return False

# --- Buyer CRUD ---

def get_buyers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Buyer).offset(skip).limit(limit).all()

def create_buyer(db: Session, buyer: schemas.BuyerCreate):
    db_buyer = models.Buyer(**buyer.model_dump())
    db.add(db_buyer)
    db.commit()
    db.refresh(db_buyer)
    return db_buyer

def delete_buyer(db: Session, buyer_id: int):
    db_buyer = db.query(models.Buyer).filter(models.Buyer.id == buyer_id).first()
    if db_buyer:
        db.delete(db_buyer)
        db.commit()
        return True
    return False
