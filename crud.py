from sqlalchemy.orm import Session, joinedload

from sqlalchemy import case
from typing import List, Optional
from datetime import date

import models, schemas
import storage

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
        models.Listing.created_at.desc()
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
        # Delete media from storage (MinIO)
        for m in listing.media:
            if m.public_id:
                try:
                    storage.delete_file(m.public_id)
                except Exception as e:
                    print(f"Failed to delete {m.public_id} from MinIO: {e}")
        
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
    if data.get("url"):
        data["url"] = data["url"].strip()
    
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
    if update_data.get("url"):
        update_data["url"] = update_data["url"].strip()
    
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

# --- Concierge Services CRUD & Sync ---
import urllib.request
from datetime import datetime

def get_concierge_properties(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.ConciergeProperty).offset(skip).limit(limit).all()

def get_concierge_property(db: Session, property_id: int):
    return db.query(models.ConciergeProperty).filter(models.ConciergeProperty.id == property_id).first()

def create_concierge_property(db: Session, property: schemas.ConciergePropertyCreate):
    db_prop = models.ConciergeProperty(**property.model_dump())
    db.add(db_prop)
    db.commit()
    db.refresh(db_prop)
    return db_prop

def update_concierge_property(db: Session, property_id: int, property_update: schemas.ConciergePropertyUpdate):
    db_prop = db.query(models.ConciergeProperty).filter(models.ConciergeProperty.id == property_id).first()
    if not db_prop:
        return None
    
    update_data = property_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_prop, key, value)
        
    db.commit()
    db.refresh(db_prop)
    return db_prop

def delete_concierge_property(db: Session, property_id: int):
    db_prop = db.query(models.ConciergeProperty).filter(models.ConciergeProperty.id == property_id).first()
    if db_prop:
        db.delete(db_prop)
        db.commit()
        return True
    return False

def sync_concierge_bookings(db: Session, property_id: int):
    return True

def calculate_financials(price, platform_fee, commission_rate, start_date, end_date):
    p = float(price or 0.0)
    pf = float(platform_fee or 0.0)
    cr = float(commission_rate or 20.0)
    
    net = p - pf
    doorman = net * (cr / 100.0)
    owner = net - doorman
    
    if start_date and end_date:
        delta = end_date - start_date
        nights = max(1, delta.days)
    else:
        nights = 1
        
    return nights, doorman, owner

def create_concierge_booking(db: Session, booking: schemas.ConciergeBookingCreate, property_id: int):
    # Check for overlapping reservation
    overlapping = db.query(models.ConciergeBooking).filter(
        models.ConciergeBooking.property_id == property_id,
        models.ConciergeBooking.start_date < booking.end_date,
        models.ConciergeBooking.end_date > booking.start_date
    ).first()
    if overlapping:
        raise ValueError("Overlapping reservation exists for this property on these dates.")

    nights, doorman, owner = calculate_financials(
        booking.price,
        booking.platform_fee,
        booking.commission_rate,
        booking.start_date,
        booking.end_date
    )

    if booking.is_block:
        summary = booking.summary or "Blocked Period"
    else:
        summary = booking.guest_name or "Direct Booking"
        if booking.price:
            summary += f" (€{booking.price})"
        
    db_booking = models.ConciergeBooking(
        property_id=property_id,
        start_date=booking.start_date,
        end_date=booking.end_date,
        summary=summary,
        guest_name=booking.guest_name if not booking.is_block else "Blocked",
        price=booking.price,
        is_manual=True,
        is_block=booking.is_block,
        source=booking.platform or "manual",
        platform=booking.platform or "resaoff",
        platform_fee=booking.platform_fee,
        commission_rate=booking.commission_rate,
        doorman_commission=doorman,
        owner_payout=owner,
        nights=nights,
        notes=booking.notes
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking

def update_concierge_booking(db: Session, booking_id: int, booking_update: schemas.ConciergeBookingUpdate):
    db_booking = db.query(models.ConciergeBooking).filter(models.ConciergeBooking.id == booking_id).first()
    if not db_booking:
        return None

    # Check for overlapping reservation (excluding the one being updated)
    start_date = booking_update.start_date if booking_update.start_date is not None else db_booking.start_date
    end_date = booking_update.end_date if booking_update.end_date is not None else db_booking.end_date
    overlapping = db.query(models.ConciergeBooking).filter(
        models.ConciergeBooking.property_id == db_booking.property_id,
        models.ConciergeBooking.id != booking_id,
        models.ConciergeBooking.start_date < end_date,
        models.ConciergeBooking.end_date > start_date
    ).first()
    if overlapping:
        raise ValueError("Overlapping reservation exists for this property on these dates.")

    if booking_update.start_date is not None:
        db_booking.start_date = booking_update.start_date
    if booking_update.end_date is not None:
        db_booking.end_date = booking_update.end_date
    if booking_update.guest_name is not None:
        db_booking.guest_name = booking_update.guest_name
    if booking_update.price is not None:
        db_booking.price = booking_update.price
    if booking_update.platform is not None:
        db_booking.platform = booking_update.platform
        if booking_update.platform in ("airbnb", "booking"):
            db_booking.source = booking_update.platform
        else:
            db_booking.source = "manual"
            
    if booking_update.platform_fee is not None:
        db_booking.platform_fee = booking_update.platform_fee
    if booking_update.commission_rate is not None:
        db_booking.commission_rate = booking_update.commission_rate
    if booking_update.is_block is not None:
        db_booking.is_block = booking_update.is_block
    if booking_update.notes is not None:
        db_booking.notes = booking_update.notes
        
    nights, doorman, owner = calculate_financials(
        db_booking.price,
        db_booking.platform_fee,
        db_booking.commission_rate,
        db_booking.start_date,
        db_booking.end_date
    )
    
    db_booking.nights = nights
    db_booking.doorman_commission = doorman
    db_booking.owner_payout = owner
    
    if db_booking.is_block:
        summary = "Blocked Period"
    else:
        summary = db_booking.guest_name or "Direct Booking"
        if db_booking.price:
            summary += f" (€{db_booking.price})"
    db_booking.summary = summary
    
    db.commit()
    db.refresh(db_booking)
    return db_booking

def delete_concierge_booking(db: Session, booking_id: int):
    db_booking = db.query(models.ConciergeBooking).filter(models.ConciergeBooking.id == booking_id).first()
    if db_booking:
        db.delete(db_booking)
        db.commit()
        return True
    return False

def unblock_calendar_range(db: Session, property_id: int, start_date: date, end_date: date):
    # Find overlapping blocks (only where is_block is True)
    blocks = db.query(models.ConciergeBooking).filter(
        models.ConciergeBooking.property_id == property_id,
        models.ConciergeBooking.is_block == True,
        models.ConciergeBooking.start_date < end_date,
        models.ConciergeBooking.end_date > start_date
    ).all()
    
    for b in blocks:
        # Case 1: Block is fully inside the unblock range -> delete it
        if b.start_date >= start_date and b.end_date <= end_date:
            db.delete(b)
            
        # Case 2: Block starts before and ends after -> split into two
        elif b.start_date < start_date and b.end_date > end_date:
            orig_end = b.end_date
            b.end_date = start_date # shrink first block
            b.nights = (b.end_date - b.start_date).days
            
            # create second block
            new_block = models.ConciergeBooking(
                property_id=property_id,
                start_date=end_date,
                end_date=orig_end,
                summary=b.summary,
                guest_name=b.guest_name,
                is_block=True,
                is_manual=True,
                source=b.source,
                platform=b.platform,
                nights=(orig_end - end_date).days,
                notes=b.notes
            )
            db.add(new_block)
            
        # Case 3: Block starts before and ends within the range -> shrink end date
        elif b.start_date < start_date and b.end_date <= end_date:
            b.end_date = start_date
            b.nights = (b.end_date - b.start_date).days
            
        # Case 4: Block starts within and ends after the range -> shrink start date
        elif b.start_date >= start_date and b.end_date > end_date:
            b.start_date = end_date
            b.nights = (b.end_date - b.start_date).days

    db.commit()
    return True

# ── Cleaner CRUD ───────────────────────────────────────────────────────────

def get_cleaners(db: Session):
    return db.query(models.Cleaner).order_by(models.Cleaner.name).all()

def create_cleaner(db: Session, cleaner: schemas.CleanerCreate):
    db_cleaner = models.Cleaner(
        name=cleaner.name,
        phone=cleaner.phone,
        hourly_rate=cleaner.hourly_rate,
    )
    db.add(db_cleaner)
    db.commit()
    db.refresh(db_cleaner)
    return db_cleaner

def update_cleaner(db: Session, cleaner_id: int, cleaner_update: schemas.CleanerUpdate):
    db_cleaner = db.query(models.Cleaner).filter(models.Cleaner.id == cleaner_id).first()
    if not db_cleaner:
        return None
    for field, value in cleaner_update.model_dump(exclude_unset=True).items():
        setattr(db_cleaner, field, value)
    db.commit()
    db.refresh(db_cleaner)
    return db_cleaner

def delete_cleaner(db: Session, cleaner_id: int):
    db_cleaner = db.query(models.Cleaner).filter(models.Cleaner.id == cleaner_id).first()
    if db_cleaner:
        db.delete(db_cleaner)
        db.commit()
        return True
    return False

# ── CleaningAssignment CRUD ────────────────────────────────────────────────

def get_cleaning_assignments(db: Session, cleaning_date: str = None):
    query = db.query(models.CleaningAssignment).options(
        joinedload(models.CleaningAssignment.cleaner),
        joinedload(models.CleaningAssignment.property)
    )
    if cleaning_date:
        from datetime import date
        query = query.filter(models.CleaningAssignment.cleaning_date == cleaning_date)
    return query.order_by(models.CleaningAssignment.cleaning_date).all()

def create_cleaning_assignment(db: Session, assignment: schemas.CleaningAssignmentCreate):
    cleaner = db.query(models.Cleaner).filter(models.Cleaner.id == assignment.cleaner_id).first()
    prop = db.query(models.ConciergeProperty).filter(models.ConciergeProperty.id == assignment.property_id).first()
    db_assignment = models.CleaningAssignment(
        cleaner_id=assignment.cleaner_id,
        property_id=assignment.property_id,
        cleaning_date=assignment.cleaning_date,
        notes=assignment.notes,
        hourly_rate=assignment.hourly_rate if assignment.hourly_rate is not None else (cleaner.hourly_rate if cleaner else None),
        max_cleaning_duration=assignment.max_cleaning_duration if assignment.max_cleaning_duration is not None else (prop.max_cleaning_duration if prop else None),
        airbnb_cleaning_fee=assignment.airbnb_cleaning_fee if assignment.airbnb_cleaning_fee is not None else (prop.airbnb_cleaning_fee if prop else None),
    )
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    return db.query(models.CleaningAssignment).options(
        joinedload(models.CleaningAssignment.cleaner),
        joinedload(models.CleaningAssignment.property)
    ).filter(models.CleaningAssignment.id == db_assignment.id).first()

def update_cleaning_assignment(db: Session, assignment_id: int, update: schemas.CleaningAssignmentUpdate):
    db_a = db.query(models.CleaningAssignment).filter(models.CleaningAssignment.id == assignment_id).first()
    if not db_a:
        return None
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_a, field, value)
    if "cleaner_id" in update_data and "hourly_rate" not in update_data:
        cleaner = db.query(models.Cleaner).filter(models.Cleaner.id == db_a.cleaner_id).first()
        db_a.hourly_rate = cleaner.hourly_rate if cleaner else None
    if "property_id" in update_data:
        prop = db.query(models.ConciergeProperty).filter(models.ConciergeProperty.id == db_a.property_id).first()
        if prop:
            if "max_cleaning_duration" not in update_data:
                db_a.max_cleaning_duration = prop.max_cleaning_duration
            if "airbnb_cleaning_fee" not in update_data:
                db_a.airbnb_cleaning_fee = prop.airbnb_cleaning_fee
    db.commit()
    db.refresh(db_a)
    return db_a

def delete_cleaning_assignment(db: Session, assignment_id: int):
    db_a = db.query(models.CleaningAssignment).filter(models.CleaningAssignment.id == assignment_id).first()
    if db_a:
        db.delete(db_a)
        db.commit()
        return True
    return False

def get_concierge_reports(db: Session):
    return db.query(models.ConciergeReport).all()

def update_or_create_concierge_report(db: Session, property_id: int, year: int, month: int, status: str, last_sent_at = None):
    db_report = db.query(models.ConciergeReport).filter(
        models.ConciergeReport.property_id == property_id,
        models.ConciergeReport.year == year,
        models.ConciergeReport.month == month
    ).first()
    
    if not db_report:
        db_report = models.ConciergeReport(
            property_id=property_id,
            year=year,
            month=month,
            status=status,
            last_sent_at=last_sent_at
        )
        db.add(db_report)
    else:
        db_report.status = status
        if last_sent_at:
            db_report.last_sent_at = last_sent_at
            
    db.commit()
    db.refresh(db_report)
    return db_report


# ── CleanerTransaction CRUD ────────────────────────────────────────────────

def get_cleaner_transactions(db: Session, skip: int = 0, limit: int = 1000):
    return (
        db.query(models.CleanerTransaction)
        .order_by(models.CleanerTransaction.transaction_date.desc(), models.CleanerTransaction.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_cleaner_transaction(db: Session, transaction: schemas.CleanerTransactionCreate):
    db_transaction = models.CleanerTransaction(**transaction.model_dump())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


def delete_cleaner_transaction(db: Session, transaction_id: int):
    db_transaction = (
        db.query(models.CleanerTransaction)
        .filter(models.CleanerTransaction.id == transaction_id)
        .first()
    )
    if db_transaction:
        db.delete(db_transaction)
        db.commit()
        return True
    return False


def update_cleaner_transaction(db: Session, transaction_id: int, transaction_update: schemas.CleanerTransactionCreate):
    db_transaction = (
        db.query(models.CleanerTransaction)
        .filter(models.CleanerTransaction.id == transaction_id)
        .first()
    )
    if not db_transaction:
        return None
    for key, value in transaction_update.model_dump().items():
        setattr(db_transaction, key, value)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction
