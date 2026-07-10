from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Text, Boolean, DateTime, Table, Date

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import database

class Listing(database.Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    price = Column(Numeric(precision=12, scale=2))
    listing_type = Column(String)  # buy/rent
    status = Column(String, default="active")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_by = relationship("User", foreign_keys=[created_by_id])
    updated_by = relationship("User", foreign_keys=[updated_by_id])
    details = relationship("PropertyDetails", back_populates="listing", uselist=False, cascade="all, delete-orphan")
    media = relationship("Media", back_populates="listing", cascade="all, delete-orphan")

class PropertyDetails(database.Base):
    __tablename__ = "property_details"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), unique=True)
    
    description = Column(Text)
    description_en = Column(Text, nullable=True)
    description_fr = Column(Text, nullable=True)
    description_tr = Column(Text, nullable=True)
    bedrooms = Column(Integer)
    bathrooms = Column(Integer)
    sqft = Column(Numeric(precision=10, scale=2))
    address = Column(String)
    neighborhood = Column(String, nullable=True, index=True)
    property_type = Column(String, nullable=True, index=True) # Apartment, Villa, etc.
    lat = Column(Numeric(precision=18, scale=14), nullable=True)
    lng = Column(Numeric(precision=18, scale=14), nullable=True)
    energy_class = Column(String, nullable=True)  # A, B, C...
    has_parking = Column(Boolean, default=False)
    has_balcony = Column(Boolean, default=False)
    has_cave = Column(Boolean, default=False)
    has_elevator = Column(Boolean, default=False)
    floor = Column(Integer, nullable=True)
    total_floors = Column(Integer, nullable=True)
    available_date = Column(String, nullable=True)
    transport_info = Column(String, nullable=True)
    
    listing = relationship("Listing", back_populates="details")

class Media(database.Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"))
    url = Column(String)
    public_id = Column(String, nullable=True)
    media_type = Column(String, default="image")
    is_thumbnail = Column(Boolean, default=False)

    listing = relationship("Listing", back_populates="media")

class User(database.Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    role = Column(String, default="editor") # superuser / editor
    is_active = Column(Boolean, default=True)
    must_change_password = Column(Boolean, default=True)

class PasswordResetRequest(database.Base):
    __tablename__ = "password_reset_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="pending") # pending, approved, rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")

class BlogPost(database.Base):
    __tablename__ = "blog_posts"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True)
    
    title_en = Column(String)
    title_fr = Column(String, nullable=True)
    title_tr = Column(String, nullable=True)
    
    content_en = Column(Text)
    content_fr = Column(Text, nullable=True)
    content_tr = Column(Text, nullable=True)
    
    excerpt_en = Column(String, nullable=True)
    excerpt_fr = Column(String, nullable=True)
    excerpt_tr = Column(String, nullable=True)
    
    image_url = Column(String, nullable=True)
    published_at = Column(DateTime(timezone=True), server_default=func.now())
    is_published = Column(Boolean, default=True)
    is_approved = Column(Boolean, default=False)
    
    author_id = Column(Integer, ForeignKey("users.id"))
    author = relationship("User")

class ContactMessage(database.Base):
    __tablename__ = "contact_messages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    phone = Column(String, nullable=True)
    message = Column(Text)
    property_id = Column(Integer, nullable=True)
    property_title = Column(String, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Buyer(database.Base):
    __tablename__ = "buyers"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Many-to-many association table for ResearchListing and ResearchTag
research_listing_tags = Table(
    "research_listing_tags",
    database.Base.metadata,
    Column("research_listing_id", Integer, ForeignKey("research_listings.id", ondelete="CASCADE")),
    Column("tag_id", Integer, ForeignKey("research_tags.id", ondelete="CASCADE"))
)

class ResearchTag(database.Base):
    __tablename__ = "research_tags"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

class ResearchListing(database.Base):
    __tablename__ = "research_listings"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False, unique=True)

    rooms = Column(Integer, nullable=False)
    address = Column(String, nullable=True)

    neighborhood = Column(String, nullable=False)
    zip_code = Column(String, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    buyer_id = Column(Integer, ForeignKey("buyers.id"), nullable=True)
    dpe = Column(String, nullable=True) # Energy class (A, B, C...)

    price = Column(Numeric(precision=12, scale=2), nullable=False)

    square_meters = Column(Numeric(precision=10, scale=2), nullable=False)
    price_per_sqm = Column(Numeric(precision=12, scale=2), nullable=True)
    has_balcony = Column(Boolean, default=False)
    has_parking = Column(Boolean, default=False)
    has_garden = Column(Boolean, default=False)
    has_elevator = Column(Boolean, default=False)
    floor = Column(Integer, nullable=True)
    total_floors = Column(Integer, nullable=True)
    heating_system = Column(String, nullable=True)
    internal_notes = Column(Text, nullable=True)




    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    created_by = relationship("User")
    buyer = relationship("Buyer")
    tags = relationship("ResearchTag", secondary=research_listing_tags, backref="listings")

class ConciergeProperty(database.Base):
    __tablename__ = "concierge_properties"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    address = Column(String, nullable=True)
    owner_name = Column(String, nullable=True)
    owner_email = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    bookings = relationship("ConciergeBooking", back_populates="property", cascade="all, delete-orphan")

class ConciergeBooking(database.Base):
    __tablename__ = "concierge_bookings"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("concierge_properties.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    summary = Column(String, nullable=True)
    uid = Column(String, nullable=True)
    price = Column(Numeric(10, 2), nullable=True)
    guest_name = Column(String, nullable=True)
    is_manual = Column(Boolean, default=True)
    source = Column(String, nullable=False, default="manual")
    platform = Column(String, default="resaoff")
    platform_fee = Column(Numeric(10, 2), default=0.0)
    commission_rate = Column(Numeric(5, 2), default=20.0)
    owner_payout = Column(Numeric(10, 2), default=0.0)
    doorman_commission = Column(Numeric(10, 2), default=0.0)
    nights = Column(Integer, default=1)

    property = relationship("ConciergeProperty", back_populates="bookings")

class Cleaner(database.Base):
    __tablename__ = "cleaners"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    hourly_rate = Column(Numeric(10, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    assignments = relationship("CleaningAssignment", back_populates="cleaner", cascade="all, delete-orphan")

class CleaningAssignment(database.Base):
    __tablename__ = "cleaning_assignments"

    id = Column(Integer, primary_key=True, index=True)
    cleaner_id = Column(Integer, ForeignKey("cleaners.id", ondelete="CASCADE"), nullable=False)
    property_id = Column(Integer, ForeignKey("concierge_properties.id", ondelete="CASCADE"), nullable=False)
    cleaning_date = Column(Date, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    cleaner = relationship("Cleaner", back_populates="assignments")
    property = relationship("ConciergeProperty")


class ConciergeReport(database.Base):
    __tablename__ = "concierge_reports"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("concierge_properties.id", ondelete="CASCADE"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    status = Column(String, default="not_sent")
    last_sent_at = Column(DateTime(timezone=True), nullable=True)

    property = relationship("ConciergeProperty")
