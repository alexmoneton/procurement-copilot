"""Database models for the procurement copilot system."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Union

from sqlalchemy import ARRAY, Boolean, Column, Date, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class TenderSource(str, Enum):
    """Tender source enumeration."""

    TED = "TED"
    BOAMP_FR = "BOAMP_FR"

    # European platforms
    GERMANY = "GERMANY"
    ITALY = "ITALY"
    SPAIN = "SPAIN"
    NETHERLANDS = "NETHERLANDS"
    UK = "UK"
    DENMARK = "DENMARK"
    FINLAND = "FINLAND"
    SWEDEN = "SWEDEN"
    AUSTRIA = "AUSTRIA"

    # Nordic sub-platforms
    NORDIC_DK = "NORDIC_DK"
    NORDIC_FI = "NORDIC_FI"
    NORDIC_SE = "NORDIC_SE"


class NotifyFrequency(str, Enum):
    """Notification frequency enumeration."""

    DAILY = "daily"
    WEEKLY = "weekly"


class Tender(Base):
    """Tender model for storing procurement opportunities."""

    __tablename__ = "tenders"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    # Tender identification
    tender_ref: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique tender reference number",
    )
    source: Mapped[TenderSource] = mapped_column(
        SQLEnum(TenderSource),
        nullable=False,
        index=True,
        comment="Source of the tender (TED, BOAMP_FR, European platforms)",
    )

    # Tender details
    title: Mapped[str] = mapped_column(Text, nullable=False, comment="Tender title")
    summary: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Tender summary/description"
    )

    # Dates
    publication_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True, comment="Date when tender was published"
    )
    deadline_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, index=True, comment="Deadline for tender submission"
    )

    # CPV codes and buyer information
    cpv_codes: Mapped[list[str]] = mapped_column(
        ARRAY(String(10)),
        nullable=False,
        default=list,
        comment="CPV (Common Procurement Vocabulary) codes",
    )
    buyer_name: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Name of the buying organization"
    )
    buyer_country: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        index=True,
        comment="Buyer country code (ISO 3166-1 alpha-2)",
    )

    # Financial information
    value_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True, comment="Estimated tender value amount"
    )
    currency: Mapped[Optional[str]] = mapped_column(
        String(3), nullable=True, comment="Currency code (ISO 4217)"
    )

    # External reference
    url: Mapped[str] = mapped_column(
        Text, nullable=False, comment="URL to the original tender notice"
    )
    raw_blob: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Raw data blob from the source for debugging/reprocessing",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Record last update timestamp",
    )

    # Indexes
    __table_args__ = (
        Index("ix_tenders_cpv_codes", "cpv_codes", postgresql_using="gin"),
        Index(
            "ix_tenders_publication_date_desc",
            "publication_date",
            postgresql_using="btree",
        ),
        Index(
            "ix_tenders_deadline_date_desc", "deadline_date", postgresql_using="btree"
        ),
        Index("ix_tenders_buyer_country", "buyer_country", postgresql_using="btree"),
    )


class User(Base):
    """User model for authentication and personalization."""

    __tablename__ = "users"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    # User details
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User email address",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="User registration timestamp",
    )

    # Relationships
    saved_filters: Mapped[list["SavedFilter"]] = relationship(
        "SavedFilter",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )


class UserProfile(Base):
    """User profile model for personalization."""

    __tablename__ = "user_profiles"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    # Foreign key
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="User ID",
    )

    # Profile details
    company_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Company name"
    )
    target_value_range: Mapped[Optional[list[int]]] = mapped_column(
        ARRAY(Integer), nullable=True, comment="Target value range [min, max]"
    )
    preferred_countries: Mapped[Optional[list[str]]] = mapped_column(
        ARRAY(String(2)), nullable=True, comment="Preferred countries"
    )
    cpv_expertise: Mapped[Optional[list[str]]] = mapped_column(
        ARRAY(String(10)), nullable=True, comment="CPV expertise codes"
    )
    company_size: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Company size"
    )
    experience_level: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Experience level"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Profile creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Profile last update timestamp",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="profile",
    )


class SavedFilter(Base):
    """Saved filter model for user preferences."""

    __tablename__ = "saved_filters"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    # Foreign key
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Filter name and criteria
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Human-readable name for the filter"
    )
    keywords: Mapped[list[str]] = mapped_column(
        ARRAY(String(100)),
        nullable=False,
        default=list,
        comment="Keywords to search for in tender titles/summaries",
    )
    cpv_codes: Mapped[list[str]] = mapped_column(
        ARRAY(String(10)),
        nullable=False,
        default=list,
        comment="CPV codes to filter by",
    )
    countries: Mapped[list[str]] = mapped_column(
        ARRAY(String(2)),
        nullable=False,
        default=list,
        comment="Country codes to filter by",
    )

    # Value range
    min_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True, comment="Minimum tender value"
    )
    max_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True, comment="Maximum tender value"
    )

    # Notification settings
    notify_frequency: Mapped[NotifyFrequency] = mapped_column(
        SQLEnum(NotifyFrequency),
        nullable=False,
        default=NotifyFrequency.DAILY,
        comment="How often to send notifications",
    )
    last_notified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last time notification was sent for this filter",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Filter creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Filter last update timestamp",
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="saved_filters")
    email_logs: Mapped[list["EmailLog"]] = relationship(
        "EmailLog",
        back_populates="saved_filter",
        cascade="all, delete-orphan",
    )


class EmailLog(Base):
    """Email log model for tracking sent notifications."""

    __tablename__ = "email_logs"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    # Foreign keys
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    saved_filter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("saved_filters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Email content
    subject: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="Email subject line"
    )
    body_preview: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="First 200 characters of email body for preview",
    )

    # Timestamps
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="When the email was sent",
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    saved_filter: Mapped["SavedFilter"] = relationship(
        "SavedFilter", back_populates="email_logs"
    )


class Award(Base):
    """Award model for storing tender award information."""

    __tablename__ = "awards"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    # Foreign key to tender
    tender_ref: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("tenders.tender_ref", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the awarded tender",
    )

    # Award information
    award_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True, comment="Date when the award was made"
    )
    winner_names: Mapped[list[str]] = mapped_column(
        ARRAY(String(255)),
        nullable=False,
        default=list,
        comment="Names of winning suppliers",
    )
    other_bidders: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(255)),
        nullable=True,
        comment="Names of other bidders (if available)",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Record last update timestamp",
    )

    # Relationships
    tender: Mapped["Tender"] = relationship(
        "Tender",
        foreign_keys=[tender_ref],
        primaryjoin="Award.tender_ref == Tender.tender_ref",
    )


class Company(Base):
    """Company model for storing supplier information."""

    __tablename__ = "companies"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    # Company information
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True, comment="Company name"
    )
    domain: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True, comment="Company website domain"
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Primary contact email"
    )
    country: Mapped[str] = mapped_column(
        String(2), nullable=False, index=True, comment="Company country code"
    )

    # Metadata
    is_suppressed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether company is on suppression list",
    )
    last_contacted: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last time company was contacted",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Record last update timestamp",
    )

    # Table constraints
    __table_args__ = (
        Index("ix_companies_name_country", "name", "country"),
        Index("ix_companies_domain", "domain"),
    )
