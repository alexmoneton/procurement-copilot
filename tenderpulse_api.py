#!/usr/bin/env python3
"""
TenderPulse API - Production-ready version with connector architecture.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add backend to path
sys.path.insert(0, 'backend')

# Set environment for TED-only mode
os.environ['ENABLE_CONNECTORS'] = 'TED'
os.environ['SHADOW_CONNECTORS'] = ''

# Import connector system
from backend.app.scrapers.registry import resolve_enabled, enabled_source_names, shadow_source_names
from backend.app.scrapers.base import normalize_record

app = FastAPI(
    title="TenderPulse API",
    description="Real-time signals for European public contracts",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TenderResponse(BaseModel):
    tender_ref: str
    source: str
    is_shadow: bool
    title: str
    summary: Optional[str]
    publication_date: date
    deadline_date: Optional[date]
    cpv_codes: List[str]
    buyer_name: Optional[str]
    buyer_country: str
    value_amount: Optional[float]
    currency: Optional[str]
    url: str

class TendersListResponse(BaseModel):
    tenders: List[TenderResponse]
    total: int
    page: int
    limit: int

class HealthResponse(BaseModel):
    status: str
    message: str
    timestamp: datetime
    version: str
    enabled_sources: List[str]
    shadow_sources: List[str]

class MetricsResponse(BaseModel):
    tenders_ingested_total: Dict[str, int]
    enabled_sources: List[str]
    shadow_sources: List[str]
    last_ingest: Optional[datetime]

# In-memory cache for demo (in production, this would be database)
_tender_cache: List[Dict[str, Any]] = []
_last_fetch: Optional[datetime] = None

async def get_fresh_tenders(limit: int = 100) -> List[Dict[str, Any]]:
    """Get fresh tenders from connectors."""
    global _tender_cache, _last_fetch
    
    # Refresh cache if older than 1 hour
    if not _last_fetch or datetime.now() - _last_fetch > timedelta(hours=1):
        enabled_connectors, shadow_connectors = resolve_enabled()
        all_tenders = []
        since = datetime.now() - timedelta(days=7)  # Last week
        
        # Fetch from enabled connectors
        for connector in enabled_connectors:
            try:
                notices = await connector.fetch_since(since, limit)
                for notice in notices:
                    tender_data = normalize_record(notice)
                    tender_data["is_shadow"] = False
                    all_tenders.append(tender_data)
            except Exception as e:
                print(f"Error with connector {connector.name}: {e}")
        
        # Fetch from shadow connectors  
        for connector in shadow_connectors:
            try:
                notices = await connector.fetch_since(since, limit)
                for notice in notices:
                    tender_data = normalize_record(notice)
                    tender_data["is_shadow"] = True
                    all_tenders.append(tender_data)
            except Exception as e:
                print(f"Error with shadow connector {connector.name}: {e}")
        
        _tender_cache = all_tenders
        _last_fetch = datetime.now()
    
    return _tender_cache

@app.get("/", response_model=dict)
async def root():
    """Root endpoint."""
    return {
        "message": "TenderPulse API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "enabled_sources": enabled_source_names(),
        "shadow_sources": shadow_source_names()
    }

@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="TenderPulse API is operational",
        timestamp=datetime.now(),
        version="1.0.0",
        enabled_sources=enabled_source_names(),
        shadow_sources=shadow_source_names()
    )

@app.get("/api/v1/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get metrics for monitoring."""
    tenders = await get_fresh_tenders()
    
    # Count by source
    source_counts = {}
    for tender in tenders:
        source = tender.get("source", "unknown")
        source_counts[source] = source_counts.get(source, 0) + 1
    
    return MetricsResponse(
        tenders_ingested_total=source_counts,
        enabled_sources=enabled_source_names(),
        shadow_sources=shadow_source_names(),
        last_ingest=_last_fetch
    )

@app.get("/api/v1/tenders", response_model=TendersListResponse)
async def get_tenders(
    limit: int = Query(default=20, ge=1, le=100, description="Number of tenders to return"),
    page: int = Query(default=1, ge=1, description="Page number"),
    query: Optional[str] = Query(default=None, description="Search query"),
    country: Optional[str] = Query(default=None, description="Filter by country"),
    min_value: Optional[float] = Query(default=None, description="Minimum tender value"),
    max_value: Optional[float] = Query(default=None, description="Maximum tender value"),
    cpv: Optional[str] = Query(default=None, description="CPV code filter")
):
    """Get procurement tenders with filtering and pagination."""
    try:
        # Get all tenders
        all_tenders = await get_fresh_tenders()
        
        # Filter out shadow tenders (only show enabled sources)
        visible_tenders = [t for t in all_tenders if not t.get("is_shadow", False)]
        
        # Convert to response format
        tenders = []
        for tender in visible_tenders:
            tender_response = TenderResponse(
                tender_ref=tender.get("tender_ref", ""),
                source=tender.get("source", "TED"),
                is_shadow=tender.get("is_shadow", False),
                title=tender.get("title", ""),
                summary=tender.get("summary"),
                publication_date=tender.get("publication_date", date.today()),
                deadline_date=tender.get("deadline_date"),
                cpv_codes=tender.get("cpv_codes", []),
                buyer_name=tender.get("buyer_name"),
                buyer_country=tender.get("buyer_country", ""),
                value_amount=tender.get("value_amount"),
                currency=tender.get("currency", "EUR"),
                url=tender.get("url", "")
            )
            tenders.append(tender_response)
        
        # Apply filters
        filtered_tenders = tenders
        
        if query:
            filtered_tenders = [
                t for t in filtered_tenders 
                if query.lower() in t.title.lower() or (t.summary and query.lower() in t.summary.lower())
            ]
        
        if country:
            filtered_tenders = [
                t for t in filtered_tenders 
                if t.buyer_country.upper() == country.upper()
            ]
        
        if min_value and isinstance(min_value, (int, float)):
            filtered_tenders = [
                t for t in filtered_tenders 
                if t.value_amount and t.value_amount >= min_value
            ]
        
        if max_value and isinstance(max_value, (int, float)):
            filtered_tenders = [
                t for t in filtered_tenders 
                if t.value_amount and t.value_amount <= max_value
            ]
        
        if cpv:
            filtered_tenders = [
                t for t in filtered_tenders 
                if any(cpv.upper() in code.upper() for code in t.cpv_codes)
            ]
        
        # Pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_tenders = filtered_tenders[start_idx:end_idx]
        
        return TendersListResponse(
            tenders=paginated_tenders,
            total=len(filtered_tenders),
            page=page,
            limit=limit
        )
        
    except Exception as e:
        # Return empty result on error
        return TendersListResponse(
            tenders=[],
            total=0,
            page=page,
            limit=limit
        )

@app.get("/api/v1/tenders/stats/summary")
async def get_tender_stats():
    """Get tender statistics."""
    try:
        # Get tenders (only visible ones)
        all_tenders = await get_fresh_tenders()
        visible_tenders = [t for t in all_tenders if not t.get("is_shadow", False)]
        
        countries = {}
        total_value = 0
        sources = {}
        
        for tender in visible_tenders:
            country = tender.get("buyer_country", "Unknown")
            countries[country] = countries.get(country, 0) + 1
            
            value = tender.get("value_amount", 0) or 0
            total_value += value
            
            source = tender.get("source", "Unknown")
            sources[source] = sources.get(source, 0) + 1
        
        return {
            "total_tenders": len(visible_tenders),
            "total_value": total_value,
            "countries": len(countries),
            "country_breakdown": countries,
            "source_breakdown": sources,
            "average_value": int(total_value // len(visible_tenders)) if visible_tenders else 0,
            "enabled_sources": enabled_source_names(),
            "shadow_sources": shadow_source_names()
        }
        
    except Exception as e:
        return {
            "total_tenders": 0,
            "total_value": 0,
            "countries": 0,
            "country_breakdown": {},
            "source_breakdown": {},
            "average_value": 0,
            "enabled_sources": enabled_source_names(),
            "shadow_sources": shadow_source_names()
        }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting TenderPulse API with Connector Architecture...")
    print("📊 API Documentation: http://localhost:8000/docs")
    print("🔍 Tenders Endpoint: http://localhost:8000/api/v1/tenders")
    print("📈 Stats Endpoint: http://localhost:8000/api/v1/tenders/stats/summary")
    print("💚 Health Check: http://localhost:8000/api/v1/health")
    print("📊 Metrics: http://localhost:8000/api/v1/metrics")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
