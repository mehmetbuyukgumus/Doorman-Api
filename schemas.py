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
