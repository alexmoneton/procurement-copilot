"""Pydantic schemas for API serialization."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from .models import TenderSource, NotifyFrequency


class TenderBase(BaseModel):
    """Base tender schema."""
    
    tender_ref: str = Field(..., description="Unique tender reference")
    source: TenderSource = Field(..., description="Tender source")
    title: str = Field(..., description="Tender title")
    summary: Optional[str] = Field(None, description="Tender summary")
    publication_date: date = Field(..., description="Publication date")
    deadline_date: Optional[date] = Field(None, description="Deadline date")
    cpv_codes: list[str] = Field(default_factory=list, description="CPV codes")
    buyer_name: Optional[str] = Field(None, description="Buyer name")
    buyer_country: str = Field(..., description="Buyer country code")
    value_amount: Optional[Decimal] = Field(None, description="Value amount")
    currency: Optional[str] = Field(None, description="Currency code")
    url: str = Field(..., description="Tender URL")


class TenderCreate(TenderBase):
    """Schema for creating a tender."""
    pass


class TenderUpdate(BaseModel):
    """Schema for updating a tender."""
    
    title: Optional[str] = None
    summary: Optional[str] = None
    deadline_date: Optional[date] = None
    cpv_codes: Optional[list[str]] = None
    buyer_name: Optional[str] = None
    value_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    url: Optional[str] = None


class Tender(TenderBase):
    """Schema for tender response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(..., description="Tender ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    # Intelligence fields (calculated dynamically)
    smart_score: Optional[int] = Field(None, description="Intelligence score 0-100")
    competition_level: Optional[str] = Field(None, description="Expected competition level")
    deadline_urgency: Optional[str] = Field(None, description="Deadline strategy advice")


class TenderList(BaseModel):
    """Schema for tender list response."""
    
    items: list[Tender] = Field(..., description="List of tenders")
    total: int = Field(..., description="Total number of tenders")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")


class TenderSearchParams(BaseModel):
    """Schema for tender search parameters."""
    
    query: Optional[str] = Field(None, description="Search query")
    cpv: Optional[str] = Field(None, description="CPV code filter")
    country: Optional[str] = Field(None, description="Country filter")
    from_date: Optional[date] = Field(None, description="From date filter")
    to_date: Optional[date] = Field(None, description="To date filter")
    min_value: Optional[Decimal] = Field(None, description="Minimum value filter")
    max_value: Optional[Decimal] = Field(None, description="Maximum value filter")
    source: Optional[TenderSource] = Field(None, description="Source filter")
    limit: int = Field(50, ge=1, le=100, description="Number of results to return")
    offset: int = Field(0, ge=0, description="Number of results to skip")


class UserBase(BaseModel):
    """Base user schema."""
    
    email: str = Field(..., description="User email")


class UserCreate(UserBase):
    """Schema for creating a user."""
    pass


class User(UserBase):
    """Schema for user response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Registration timestamp")


class UserProfileBase(BaseModel):
    """Base user profile schema."""
    
    company_name: Optional[str] = Field(None, description="Company name")
    target_value_range: Optional[list[int]] = Field(None, description="Target value range [min, max]")
    preferred_countries: Optional[list[str]] = Field(None, description="Preferred countries")
    cpv_expertise: Optional[list[str]] = Field(None, description="CPV expertise codes")
    company_size: Optional[str] = Field(None, description="Company size")
    experience_level: Optional[str] = Field(None, description="Experience level")


class UserProfileCreate(UserProfileBase):
    """Schema for creating a user profile."""
    pass


class UserProfileUpdate(BaseModel):
    """Schema for updating a user profile."""
    
    company_name: Optional[str] = None
    target_value_range: Optional[list[int]] = None
    preferred_countries: Optional[list[str]] = None
    cpv_expertise: Optional[list[str]] = None
    company_size: Optional[str] = None
    experience_level: Optional[str] = None


class UserProfile(UserProfileBase):
    """Schema for user profile response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(..., description="Profile ID")
    user_id: uuid.UUID = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class SavedFilterBase(BaseModel):
    """Base saved filter schema."""
    
    name: str = Field(..., description="Filter name")
    keywords: list[str] = Field(default_factory=list, description="Search keywords")
    cpv_codes: list[str] = Field(default_factory=list, description="CPV codes")
    countries: list[str] = Field(default_factory=list, description="Country codes")
    min_value: Optional[Decimal] = Field(None, description="Minimum value")
    max_value: Optional[Decimal] = Field(None, description="Maximum value")
    notify_frequency: NotifyFrequency = Field(
        NotifyFrequency.DAILY,
        description="Notification frequency"
    )


class SavedFilterCreate(SavedFilterBase):
    """Schema for creating a saved filter."""
    pass


class SavedFilterUpdate(BaseModel):
    """Schema for updating a saved filter."""
    
    name: Optional[str] = None
    keywords: Optional[list[str]] = None
    cpv_codes: Optional[list[str]] = None
    countries: Optional[list[str]] = None
    min_value: Optional[Decimal] = None
    max_value: Optional[Decimal] = None
    notify_frequency: Optional[NotifyFrequency] = None


class SavedFilter(SavedFilterBase):
    """Schema for saved filter response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(..., description="Filter ID")
    user_id: uuid.UUID = Field(..., description="User ID")
    last_notified_at: Optional[datetime] = Field(None, description="Last notification timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class EmailLogBase(BaseModel):
    """Base email log schema."""
    
    subject: str = Field(..., description="Email subject")
    body_preview: str = Field(..., description="Email body preview")


class EmailLogCreate(EmailLogBase):
    """Schema for creating an email log."""
    
    user_id: uuid.UUID = Field(..., description="User ID")
    saved_filter_id: uuid.UUID = Field(..., description="Saved filter ID")


class EmailLog(EmailLogBase):
    """Schema for email log response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(..., description="Email log ID")
    user_id: uuid.UUID = Field(..., description="User ID")
    saved_filter_id: uuid.UUID = Field(..., description="Saved filter ID")
    sent_at: datetime = Field(..., description="Sent timestamp")


class AwardBase(BaseModel):
    """Base award schema."""
    
    tender_ref: str = Field(..., description="Tender reference")
    award_date: date = Field(..., description="Award date")
    winner_names: list[str] = Field(default_factory=list, description="Winner names")
    other_bidders: Optional[list[str]] = Field(None, description="Other bidders")


class AwardCreate(AwardBase):
    """Schema for creating an award."""
    pass


class Award(AwardBase):
    """Schema for award response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(..., description="Award ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class CompanyBase(BaseModel):
    """Base company schema."""
    
    name: str = Field(..., description="Company name")
    domain: Optional[str] = Field(None, description="Company domain")
    email: Optional[str] = Field(None, description="Company email")
    country: str = Field(..., description="Company country")


class CompanyCreate(CompanyBase):
    """Schema for creating a company."""
    pass


class CompanyUpdate(BaseModel):
    """Schema for updating a company."""
    
    name: Optional[str] = None
    domain: Optional[str] = None
    email: Optional[str] = None
    country: Optional[str] = None
    is_suppressed: Optional[bool] = None


class Company(CompanyBase):
    """Schema for company response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(..., description="Company ID")
    is_suppressed: bool = Field(..., description="Whether company is suppressed")
    last_contacted: Optional[datetime] = Field(None, description="Last contact timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class HealthResponse(BaseModel):
    """Schema for health check response."""
    
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Check timestamp")
    version: str = Field(..., description="Application version")
