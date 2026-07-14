from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
import re


# ── Product Schemas ──────────────────────────────────────────────────────────

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    available: bool = True
    image_url: Optional[str] = None
    category: Optional[str] = None

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Price must be greater than 0")
        return v


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    available: Optional[bool] = None
    image_url: Optional[str] = None
    category: Optional[str] = None


class ProductOut(ProductBase):
    id: int
    business_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Business Schemas ─────────────────────────────────────────────────────────

class BusinessBase(BaseModel):
    name: str
    description: Optional[str] = None
    whatsapp_number: Optional[str] = None
    logo_url: Optional[str] = None


class BusinessCreate(BusinessBase):
    email: EmailStr
    password: str
    slug: Optional[str] = None  # auto-generated if not provided
    max_products: Optional[int] = None  # falls back to model default if unset

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class BusinessUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    whatsapp_number: Optional[str] = None
    logo_url: Optional[str] = None
    max_products: Optional[int] = None


class BusinessOut(BusinessBase):
    id: int
    slug: str
    email: str
    is_active: bool
    max_products: int
    created_at: datetime
    products: List[ProductOut] = []

    model_config = {"from_attributes": True}


class BusinessPublic(BusinessBase):
    """Public view — no email, no sensitive data"""
    slug: str
    products: List[ProductOut] = []

    model_config = {"from_attributes": True}


# ── Auth Schemas ─────────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    business_id: Optional[int] = None
