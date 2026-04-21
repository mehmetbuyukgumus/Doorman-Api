from sqlalchemy.orm import Session, joinedload

from sqlalchemy import case
from typing import List, Optional

import models, schemas
import cloudinary.uploader

def get_listings(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    listing_type: str = None,
    location: str = None,
    property_type: str = None,
    min_price: float = None,
    max_price: float = None,
    rooms: str = None
):
    query = db.query(models.Listing).join(models.PropertyDetails)
    
    if listing_type:
        query = query.filter(models.Listing.listing_type == listing_type)
    
    if location and "all" not in location.lower():
        query = query.filter(models.PropertyDetails.neighborhood.ilike(f"%{location}%"))
        
    if property_type:
        query = query.filter(models.PropertyDetails.property_type.ilike(f"%{property_type}%"))

    if min_price is not None:
        query = query.filter(models.Listing.price >= min_price)
    
    if max_price is not None:
        query = query.filter(models.Listing.price <= max_price)
        
    if rooms is not None:
        rooms_str = str(rooms).strip()
        if rooms_str.lower() in ["stüdyo", "studio", "0", ""]:
            query = query.filter(models.PropertyDetails.bedrooms >= 0)
        elif rooms_str.endswith("+"):
            try:
                val = int(rooms_str[:-1])
                query = query.filter(models.PropertyDetails.bedrooms >= val)
            except ValueError:
                pass
        elif rooms_str.isdigit():
            query = query.filter(models.PropertyDetails.bedrooms >= int(rooms_str))

    query = query.order_by(
        case(
            (models.Listing.status == "active", 0),
            else_=1
        ),
        models.Listing.created_at.asc()
    )

    return query.offset(skip).limit(limit).all()

def create_listing(db: Session, listing: schemas.ListingCreate, user_id: int = None):
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
    
    for m in listing.media:
        db_media = models.Media(
            **m.model_dump(),
            listing_id=db_listing.id
        )
        db.add(db_media)
        
    db.commit()
    db.refresh(db_listing)
    return db_listing

def update_listing(db: Session, listing_id: int, listing_update: schemas.ListingUpdate, user_id: int = None):
    db_listing = db.query(models.Listing).filter(models.Listing.id == listing_id).first()
    if not db_listing:
        return None
    
    # Update main listing fields
    update_data = listing_update.model_dump(exclude={"details", "media"}, exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_listing, key, value)
    
    if user_id:
        db_listing.updated_by_id = user_id
    
    # Update details if provided
    if listing_update.details:
        if not db_listing.details:
            db_details = models.PropertyDetails(
                **listing_update.details.model_dump(exclude_unset=True),
                listing_id=db_listing.id
            )
            db.add(db_details)
        else:
            details_data = listing_update.details.model_dump(exclude_unset=True)
            for key, value in details_data.items():
                setattr(db_listing.details, key, value)

    # Update media if provided
    if listing_update.media is not None:
        # Remove existing media
        db.query(models.Media).filter(models.Media.listing_id == listing_id).delete()
        # Add new media
        for m in listing_update.media:
            db_media = models.Media(
                **m.model_dump(),
                listing_id=db_listing.id
            )
            db.add(db_media)
    
    db.commit()
    db.refresh(db_listing)
    return db_listing

def delete_listing(db: Session, listing_id: int):
    listing = db.query(models.Listing).filter(models.Listing.id == listing_id).first()
    if listing:
        # Delete media from Cloudinary
        for m in listing.media:
            if m.public_id:
                try:
                    cloudinary.uploader.destroy(m.public_id)
                except Exception as e:
                    print(f"Failed to delete {m.public_id} from Cloudinary: {e}")
        
        db.delete(listing)
        db.commit()
        return True
    return False

# --- Contact Messages ---

def create_contact_message(db: Session, message: schemas.ContactRequest):
    db_message = models.ContactMessage(**message.model_dump())
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_contact_messages(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.ContactMessage).order_by(models.ContactMessage.created_at.desc()).offset(skip).limit(limit).all()

def update_contact_message_status(db: Session, message_id: int, status: schemas.ContactMessageUpdate):
    db_message = db.query(models.ContactMessage).filter(models.ContactMessage.id == message_id).first()
    if db_message:
        db_message.is_read = status.is_read
        db.commit()
        db.refresh(db_message)
    return db_message

def delete_contact_message(db: Session, message_id: int):
    db_message = db.query(models.ContactMessage).filter(models.ContactMessage.id == message_id).first()
    if db_message:
        db.delete(db_message)
        db.commit()
        return True
    return False
# --- Blog Post CRUD ---

def get_blog_posts(db: Session, skip: int = 0, limit: int = 100, only_published: bool = False, only_approved: bool = False):
    query = db.query(models.BlogPost)
    if only_published:
        query = query.filter(models.BlogPost.is_published == True)
    if only_approved:
        query = query.filter(models.BlogPost.is_approved == True)
    return query.order_by(models.BlogPost.published_at.desc()).offset(skip).limit(limit).all()

def get_blog_post(db: Session, post_id: int):
    return db.query(models.BlogPost).filter(models.BlogPost.id == post_id).first()

def get_blog_post_by_slug(db: Session, slug: str):
    return db.query(models.BlogPost).filter(models.BlogPost.slug == slug).first()

def create_blog_post(db: Session, post: schemas.BlogPostCreate, author_id: int, is_approved: bool = False):
    db_post = models.BlogPost(
        **post.model_dump(),
        author_id=author_id,
        is_approved=is_approved
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

def update_blog_post(db: Session, post_id: int, post_update: schemas.BlogPostUpdate):
    db_post = db.query(models.BlogPost).filter(models.BlogPost.id == post_id).first()
    if not db_post:
        return None
    
    update_data = post_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_post, key, value)
    
    db.commit()
    db.refresh(db_post)
    return db_post

def delete_blog_post(db: Session, post_id: int):
    db_post = db.query(models.BlogPost).filter(models.BlogPost.id == post_id).first()
    if db_post:
        db.delete(db_post)
        db.commit()
        return True
    return False

# --- Research Listing CRUD ---

def get_research_listings(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.ResearchListing).options(
        joinedload(models.ResearchListing.buyer), 
        joinedload(models.ResearchListing.created_by),
        joinedload(models.ResearchListing.tags)
    ).order_by(models.ResearchListing.created_at.desc()).offset(skip).limit(limit).all()


def create_research_listing(db: Session, listing: schemas.ResearchListingCreate, user_id: Optional[int] = None):
    data = listing.model_dump()
    tag_ids = data.pop("tag_ids", [])
    if user_id:
        data["created_by_id"] = user_id
    if data.get("price") and data.get("square_meters") and data.get("square_meters") > 0:
        data["price_per_sqm"] = data["price"] / data["square_meters"]
    
    db_listing = models.ResearchListing(**data)


    
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
    print(f"DEBUG: update_data keys: {list(update_data.keys())}")
    print(f"DEBUG: internal_notes value: {update_data.get('internal_notes')}")
    tag_ids = update_data.pop("tag_ids", None)

    
    for key, value in update_data.items():
        setattr(db_listing, key, value)
    
    if tag_ids is not None:
        tags = db.query(models.ResearchTag).filter(models.ResearchTag.id.in_(tag_ids)).all()
        db_listing.tags = tags

    # Recalculate price_per_sqm
    if "price" in update_data or "square_meters" in update_data:
        if db_listing.price and db_listing.square_meters and db_listing.square_meters > 0:
            db_listing.price_per_sqm = db_listing.price / db_listing.square_meters

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

# --- Buyer CRUD ---

def get_buyers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Buyer).order_by(models.Buyer.full_name).offset(skip).limit(limit).all()

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

# --- Research Tag CRUD ---

def get_research_tags(db: Session):
    return db.query(models.ResearchTag).order_by(models.ResearchTag.name).all()

def create_research_tag(db: Session, tag: schemas.ResearchTagCreate):
    db_tag = models.ResearchTag(**tag.model_dump())
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
