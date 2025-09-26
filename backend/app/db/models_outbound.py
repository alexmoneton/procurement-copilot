"""
Database models for the outbound pipeline system.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey, Index, Integer, 
    JSON, Numeric, String, Text, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class ProspectStatus(PyEnum):
    """Prospect status enumeration."""
    NEW = "new"
    ENRICHED = "enriched"
    QUEUED = "queued"
    SENT = "sent"
    BOUNCED = "bounced"
    UNSUB = "unsub"
    SUPPRESSED = "suppressed"
    INVALID = "invalid"


class ContactSource(PyEnum):
    """Contact source enumeration."""
    HUNTER = "hunter"
    GUESS = "guess"
    MANUAL = "manual"


class OutboundEvent(PyEnum):
    """Outbound event enumeration."""
    QUEUED = "queued"
    SENT = "sent"
    OPEN = "open"
    CLICK = "click"
    REPLY = "reply"
    BOUNCE = "bounce"
    COMPLAINT = "complaint"
    UNSUBSCRIBE = "unsubscribe"
    ERROR = "error"


class Prospect(Base):
    """Prospect model for tracking potential customers."""
    
    __tablename__ = "prospects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(Text, nullable=False)
    normalized_company = Column(Text, nullable=False)
    country = Column(String(2), nullable=False)  # 2-letter country code
    cpv_family = Column(Text, nullable=False)
    website = Column(Text, nullable=True)
    status = Column(Enum(ProspectStatus), default=ProspectStatus.NEW, nullable=False)
    last_award_ref = Column(Text, nullable=True)
    score = Column(Numeric(3, 2), nullable=True)  # fit/lost score 0.00-1.00
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    outbound_logs = relationship("OutboundLog", back_populates="prospect")
    
    # Indexes
    __table_args__ = (
        Index("idx_prospects_status", "status"),
        Index("idx_prospects_score", "score"),
        Index("idx_prospects_created_at", "created_at"),
        Index("idx_prospects_normalized_company", "normalized_company"),
        UniqueConstraint(
            "normalized_company", "country", "cpv_family", "last_award_ref",
            name="uq_prospects_company_country_cpv_award"
        ),
    )


class ContactCache(Base):
    """Contact cache for storing discovered emails with TTL."""
    
    __tablename__ = "contact_cache"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    normalized_company = Column(Text, nullable=False)
    domain = Column(Text, nullable=False)
    email = Column(Text, nullable=False, unique=True)
    source = Column(Enum(ContactSource), nullable=False)
    confidence = Column(Numeric(3, 2), nullable=False)  # 0.00-1.00
    discovered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)  # TTL 90 days
    
    # Indexes
    __table_args__ = (
        Index("idx_contact_cache_normalized_company", "normalized_company"),
        Index("idx_contact_cache_expires_at", "expires_at"),
        Index("idx_contact_cache_confidence", "confidence"),
    )


class Suppression(Base):
    """Suppression list for emails that should not be contacted."""
    
    __tablename__ = "suppressions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(Text, nullable=False, unique=True)
    reason = Column(Text, nullable=False)
    suppressed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index("idx_suppressions_email", "email"),
        Index("idx_suppressions_suppressed_at", "suppressed_at"),
    )


class OutboundLog(Base):
    """Outbound activity log for tracking all email events."""
    
    __tablename__ = "outbound_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prospect_id = Column(UUID(as_uuid=True), ForeignKey("prospects.id"), nullable=False)
    email = Column(Text, nullable=False)
    campaign = Column(Text, nullable=False)  # e.g., 'missed_opportunities_v1'
    event = Column(Enum(OutboundEvent), nullable=False)
    meta = Column(JSON, nullable=True)  # Additional event metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    prospect = relationship("Prospect", back_populates="outbound_logs")
    
    # Indexes
    __table_args__ = (
        Index("idx_outbound_logs_campaign", "campaign"),
        Index("idx_outbound_logs_event", "event"),
        Index("idx_outbound_logs_created_at", "created_at"),
        Index("idx_outbound_logs_prospect_id", "prospect_id"),
    )


class OutboundMetrics(Base):
    """Daily metrics for outbound pipeline performance."""
    
    __tablename__ = "outbound_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(DateTime, nullable=False)
    prospects_discovered = Column(Integer, default=0, nullable=False)
    contacts_enriched = Column(Integer, default=0, nullable=False)
    emails_sent = Column(Integer, default=0, nullable=False)
    emails_opened = Column(Integer, default=0, nullable=False)
    emails_clicked = Column(Integer, default=0, nullable=False)
    emails_replied = Column(Integer, default=0, nullable=False)
    emails_bounced = Column(Integer, default=0, nullable=False)
    emails_complained = Column(Integer, default=0, nullable=False)
    emails_unsubscribed = Column(Integer, default=0, nullable=False)
    hunter_api_calls = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index("idx_outbound_metrics_date", "date"),
        UniqueConstraint("date", name="uq_outbound_metrics_date"),
    )
