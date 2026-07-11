from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

class MediaBase(BaseModel):
    url: str
    public_id: Optional[str] = None
    media_type: str = "image"
    is_thumbnail: bool = False

class MediaCreate(MediaBase):
    pass

class Media(MediaBase):
    id: int
    listing_id: int
    model_config = ConfigDict(from_attributes=True)

class PropertyDetailsBase(BaseModel):
    description: Optional[str] = None
    description_en: Optional[str] = None
    description_fr: Optional[str] = None
    description_tr: Optional[str] = None
    bedrooms: Optional[int] = 0
    bathrooms: Optional[int] = 0
    sqft: Optional[float] = 0
    address: str
    neighborhood: Optional[str] = None
    property_type: Optional[str] = "Apartment"
    lat: Optional[Decimal] = None
    lng: Optional[Decimal] = None
    energy_class: Optional[str] = None
    has_parking: bool = False
    has_balcony: bool = False
    has_cave: bool = False
    has_elevator: bool = False
    floor: Optional[int] = None
    total_floors: Optional[int] = None
    available_date: Optional[str] = None
    transport_info: Optional[str] = None

class PropertyDetailsCreate(PropertyDetailsBase):
    pass

class PropertyDetails(PropertyDetailsBase):
    id: int
    listing_id: int
    model_config = ConfigDict(from_attributes=True)

class ListingBase(BaseModel):
    title: str
    price: Decimal
    listing_type: str
    status: str = "active"

class ListingCreate(ListingBase):
    details: PropertyDetailsCreate
    media: List[MediaCreate] = []

class PropertyDetailsUpdate(PropertyDetailsBase):
    address: Optional[str] = None

class ListingUpdate(BaseModel):
    title: Optional[str] = None
    price: Optional[Decimal] = None
    listing_type: Optional[str] = None
    status: Optional[str] = None
    details: Optional[PropertyDetailsUpdate] = None
    media: Optional[List[MediaCreate]] = None

class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None
    role: str = "editor"

class UserCreate(UserBase):
    pass

class UserSchema(UserBase):
    id: int
    is_active: bool
    must_change_password: bool
    model_config = ConfigDict(from_attributes=True)

class PasswordChange(BaseModel):
    old_password: Optional[str] = None
    new_password: str

class PasswordResetRequestSchema(BaseModel):
    id: int
    user_id: int
    status: str
    created_at: datetime
    user: UserSchema
    model_config = ConfigDict(from_attributes=True)

class Listing(ListingBase):
    id: int
    details: Optional[PropertyDetails] = None
    media: List[Media] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[UserSchema] = None
    updated_by: Optional[UserSchema] = None
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str
    must_change_password: bool = False

class TokenData(BaseModel):
    email: Optional[str] = None

class BlogPostBase(BaseModel):
    slug: str
    title_en: str
    title_fr: Optional[str] = None
    title_tr: Optional[str] = None
    
    content_en: str
    content_fr: Optional[str] = None
    content_tr: Optional[str] = None
    
    excerpt_en: Optional[str] = None
    excerpt_fr: Optional[str] = None
    excerpt_tr: Optional[str] = None
    
    image_url: Optional[str] = None
    is_published: bool = True

class BlogPostCreate(BlogPostBase):
    pass

class BlogPostUpdate(BaseModel):
    slug: Optional[str] = None
    title_en: Optional[str] = None
    title_fr: Optional[str] = None
    title_tr: Optional[str] = None
    content_en: Optional[str] = None
    content_fr: Optional[str] = None
    content_tr: Optional[str] = None
    excerpt_en: Optional[str] = None
    excerpt_fr: Optional[str] = None
    excerpt_tr: Optional[str] = None
    image_url: Optional[str] = None
    is_published: Optional[bool] = None
    is_approved: Optional[bool] = None

class BlogPost(BlogPostBase):
    id: int
    is_approved: bool
    published_at: datetime
    author_id: int
    author: Optional[UserSchema] = None
    model_config = ConfigDict(from_attributes=True)

class ContactRequest(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    message: str
    property_id: Optional[int] = None
    property_title: Optional[str] = None

class ContactMessage(ContactRequest):
    id: int
    is_read: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ContactMessageUpdate(BaseModel):
    is_read: bool

class BuyerBase(BaseModel):
    full_name: str
    email: str
    phone: Optional[str] = None

class BuyerCreate(BuyerBase):
    pass

class Buyer(BuyerBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ResearchTagBase(BaseModel):
    name: str

class ResearchTagCreate(ResearchTagBase):
    pass

class ResearchTag(ResearchTagBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ResearchListingBase(BaseModel):
    url: str
    rooms: int
    address: Optional[str] = None
    neighborhood: str
    zip_code: str
    buyer_id: Optional[int] = None
    dpe: Optional[str] = None
    price: Decimal

    square_meters: Decimal
    price_per_sqm: Optional[Decimal] = None
    has_balcony: bool = False
    has_parking: bool = False
    has_garden: bool = False
    has_elevator: bool = False
    floor: Optional[int] = None
    total_floors: Optional[int] = None

    heating_system: Optional[str] = None
    internal_notes: Optional[str] = None
    tags: List[ResearchTag] = []






class ResearchListingCreate(ResearchListingBase):
    created_by_id: Optional[int] = None
    tag_ids: List[int] = []


class ResearchListingUpdate(BaseModel):
    url: Optional[str] = None
    rooms: Optional[int] = None
    address: Optional[str] = None
    neighborhood: Optional[str] = None
    zip_code: Optional[str] = None
    buyer_id: Optional[int] = None
    dpe: Optional[str] = None
    price: Optional[Decimal] = None
    square_meters: Optional[Decimal] = None
    has_balcony: Optional[bool] = None
    has_parking: Optional[bool] = None
    has_garden: Optional[bool] = None
    has_elevator: Optional[bool] = None
    floor: Optional[int] = None
    total_floors: Optional[int] = None
    heating_system: Optional[str] = None
    internal_notes: Optional[str] = None
    tag_ids: Optional[List[int]] = None





class ResearchListing(ResearchListingBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by_id: Optional[int] = None
    created_by: Optional[UserSchema] = None
    buyer: Optional[Buyer] = None
    model_config = ConfigDict(from_attributes=True)

from datetime import date

class ConciergeBookingBase(BaseModel):
    start_date: date
    end_date: date
    summary: Optional[str] = None
    uid: Optional[str] = None
    price: Optional[Decimal] = None
    guest_name: Optional[str] = None
    is_manual: bool = True
    source: str = "manual"
    platform: Optional[str] = "resaoff"
    platform_fee: Optional[Decimal] = None
    commission_rate: Optional[Decimal] = None
    owner_payout: Optional[Decimal] = None
    doorman_commission: Optional[Decimal] = None
    nights: Optional[int] = 1

class ConciergeBookingCreate(ConciergeBookingBase):
    pass

class ConciergeBookingUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    guest_name: Optional[str] = None
    price: Optional[Decimal] = None
    platform: Optional[str] = None
    platform_fee: Optional[Decimal] = None
    commission_rate: Optional[Decimal] = None
    owner_payout: Optional[Decimal] = None
    doorman_commission: Optional[Decimal] = None
    nights: Optional[int] = None

class ConciergeBooking(ConciergeBookingBase):
    id: int
    property_id: int
    model_config = ConfigDict(from_attributes=True)

class ConciergePropertyBase(BaseModel):
    title: str
    address: Optional[str] = None
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    airbnb_cleaning_fee: Optional[float] = None
    max_cleaning_duration: Optional[float] = None

class ConciergePropertyCreate(ConciergePropertyBase):
    pass

class ConciergePropertyUpdate(BaseModel):
    title: Optional[str] = None
    address: Optional[str] = None
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    airbnb_cleaning_fee: Optional[float] = None
    max_cleaning_duration: Optional[float] = None

class ConciergeProperty(ConciergePropertyBase):
    id: int
    created_at: datetime
    bookings: List[ConciergeBooking] = []
    model_config = ConfigDict(from_attributes=True)

# ── Cleaner ────────────────────────────────────────────────────────────────
class CleanerBase(BaseModel):
    name: str
    phone: Optional[str] = None
    hourly_rate: Optional[float] = None

class CleanerCreate(CleanerBase):
    pass

class CleanerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    hourly_rate: Optional[float] = None

class Cleaner(CleanerBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# ── CleaningAssignment ─────────────────────────────────────────────────────
from datetime import date as date_type

class CleaningAssignmentBase(BaseModel):
    cleaner_id: int
    property_id: int
    cleaning_date: date_type
    notes: Optional[str] = None
    hourly_rate: Optional[float] = None
    max_cleaning_duration: Optional[float] = None
    airbnb_cleaning_fee: Optional[float] = None

class CleaningAssignmentCreate(CleaningAssignmentBase):
    pass

class CleaningAssignmentUpdate(BaseModel):
    cleaner_id: Optional[int] = None
    property_id: Optional[int] = None
    notes: Optional[str] = None
    hourly_rate: Optional[float] = None
    max_cleaning_duration: Optional[float] = None
    airbnb_cleaning_fee: Optional[float] = None

class CleaningAssignment(CleaningAssignmentBase):
    id: int
    created_at: datetime
    cleaner: Optional[Cleaner] = None
    property: Optional[ConciergeProperty] = None
    model_config = ConfigDict(from_attributes=True)


# ── ConciergeReport ────────────────────────────────────────────────────────
class ConciergeReportBase(BaseModel):
    property_id: int
    year: int
    month: int
    status: str
    last_sent_at: Optional[datetime] = None

class ConciergeReportCreate(ConciergeReportBase):
    pass

class ConciergeReportUpdate(BaseModel):
    status: Optional[str] = None
    last_sent_at: Optional[datetime] = None

class ConciergeReport(ConciergeReportBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ── CleanerTransaction ────────────────────────────────────────────────────
class CleanerTransactionBase(BaseModel):
    cleaner_id: int
    property_id: Optional[int] = None
    amount: Decimal
    type: str
    transaction_date: date_type
    description: Optional[str] = None


class CleanerTransactionCreate(CleanerTransactionBase):
    pass


class CleanerTransaction(CleanerTransactionBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
