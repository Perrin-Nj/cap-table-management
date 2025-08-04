# Shareholder-related schemas following Interface Segregation Principle

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class ShareholderProfileBase(BaseModel):
    """Base shareholder profile schema"""
    full_name: str = Field(..., min_length=2, max_length=255, description="Full name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    address: Optional[str] = Field(None, description="Address")


class ShareholderProfileCreate(ShareholderProfileBase):
    """Schema for creating shareholder profiles"""
    email: str = Field(..., description="Email for user account creation")

    @validator('email')
    def validate_email(cls, v):
        """Validate email format"""
        import re
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, v):
            raise ValueError('Invalid email format')
        return v.lower()


class ShareholderProfileUpdate(BaseModel):
    """Schema for updating shareholder profiles"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None


class ShareIssuanceBase(BaseModel):
    """Base share issuance schema"""
    number_of_shares: int = Field(..., gt=0, description="Number of shares (must be positive)")
    price_per_share: Decimal = Field(..., gt=0, description="Price per share (must be positive)")
    notes: Optional[str] = Field(None, description="Additional notes")


class ShareIssuanceCreate(ShareIssuanceBase):
    """Schema for creating share issuances"""
    shareholder_id: int = Field(..., gt=0, description="Shareholder ID")


class ShareIssuanceResponse(ShareIssuanceBase):
    """Schema for share issuance responses"""
    id: int
    shareholder_id: int
    certificate_number: str
    issued_date: datetime
    total_value: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class ShareholderProfileResponse(ShareholderProfileBase):
    """Schema for shareholder profile responses"""
    id: int
    user_id: int
    total_shares: int
    created_at: datetime
    updated_at: Optional[datetime]
    share_issuances: List[ShareIssuanceResponse] = []

    class Config:
        from_attributes = True


class ShareholderSummary(BaseModel):
    """Summary schema for admin dashboard"""
    id: int
    full_name: str
    email: str
    total_shares: int
    total_value: Decimal
    issuance_count: int

    class Config:
        from_attributes = True