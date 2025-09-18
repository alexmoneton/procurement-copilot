"""Base scraper interface and protocols for TenderPulse."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Protocol, List, Dict, Any, Optional
from dataclasses import dataclass

from pydantic import BaseModel


@dataclass
class RawNotice:
    """Raw notice data from a connector."""
    tender_ref: str
    title: str
    summary: Optional[str]
    publication_date: str  # ISO format
    deadline_date: Optional[str]  # ISO format
    cpv_codes: List[str]
    buyer_name: Optional[str]
    buyer_country: str  # 2-letter code
    value_amount: Optional[float]
    currency: Optional[str]
    url: str
    raw_data: Dict[str, Any]  # Original raw data


class Connector(Protocol):
    """Protocol for procurement data connectors."""
    
    @property
    def name(self) -> str:
        """Human-readable name of the connector."""
        ...
    
    @property
    def source(self) -> str:
        """Source identifier (matches TenderSource enum)."""
        ...
    
    async def fetch_since(self, since: datetime, limit: Optional[int] = None) -> List[RawNotice]:
        """Fetch notices published since the given datetime."""
        ...


class BaseScraper(ABC):
    """Base class for scrapers with common functionality."""
    
    def __init__(self, source: str):
        self.source = source
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        import httpx
        self.session = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "TenderPulse/1.0 (https://tenderpulse.eu)"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.aclose()
    
    @abstractmethod
    async def fetch_tenders(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch tenders from this source."""
        pass


class ScrapingError(Exception):
    """Exception raised when scraping fails."""
    pass


def normalize_record(raw: RawNotice) -> Dict[str, Any]:
    """Normalize a raw notice into TenderCreate format."""
    from datetime import date
    
    def parse_date(date_str: Optional[str]) -> Optional[date]:
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
        except Exception:
            try:
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            except Exception:
                return None
    
    return {
        "tender_ref": raw.tender_ref,
        "source": raw.source,
        "is_shadow": False,  # Will be set by ingest service based on connector type
        "title": raw.title,
        "summary": raw.summary,
        "publication_date": parse_date(raw.publication_date) or date.today(),
        "deadline_date": parse_date(raw.deadline_date),
        "cpv_codes": raw.cpv_codes,
        "buyer_name": raw.buyer_name,
        "buyer_country": raw.buyer_country,
        "value_amount": raw.value_amount,
        "currency": raw.currency or "EUR",
        "url": raw.url,
        "raw_blob": str(raw.raw_data) if raw.raw_data else None,
    }
