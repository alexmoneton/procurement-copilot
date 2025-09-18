#!/usr/bin/env python3
"""
Simple working API for Procurement Copilot - Customer Testing
This bypasses database complexity and provides immediate functionality.
"""

import asyncio
import sys
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
import random

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add backend to path
sys.path.insert(0, 'backend')

# Import our working TED scraper
from backend.app.scrapers.ted import fetch_last_tenders

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
    title: str
    summary: str
    publication_date: date
    deadline_date: date
    cpv_codes: List[str]
    buyer_name: str
    buyer_country: str
    value_amount: int
    currency: str
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

@app.get("/", response_model=dict)
async def root():
    """Root endpoint."""
    return {
        "message": "TenderPulse API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }

@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="TenderPulse API is operational",
        timestamp=datetime.now(),
        version="1.0.0"
    )

@app.get("/api/v1/tenders/tenders", response_model=TendersListResponse)
async def get_tenders(
    limit: int = Query(default=20, ge=1, le=100, description="Number of tenders to return"),
    page: int = Query(default=1, ge=1, description="Page number"),
    query: Optional[str] = Query(default=None, description="Search query"),
    country: Optional[str] = Query(default=None, description="Filter by country"),
    min_value: Optional[int] = Query(default=None, description="Minimum tender value"),
    max_value: Optional[int] = Query(default=None, description="Maximum tender value")
):
    """Get procurement tenders with filtering and pagination."""
    try:
        # Fetch tenders using our working scraper
        raw_tenders = await fetch_last_tenders(200)  # Get full dataset for filtering
        
        # Convert to response format
        tenders = []
        for tender in raw_tenders:
            tender_response = TenderResponse(
                tender_ref=tender.get("tender_ref", ""),
                source=tender.get("source", "TED"),
                title=tender.get("title", ""),
                summary=tender.get("summary", ""),
                publication_date=tender.get("publication_date", date.today()),
                deadline_date=tender.get("deadline_date", date.today() + timedelta(days=30)),
                cpv_codes=tender.get("cpv_codes", []),
                buyer_name=tender.get("buyer_name", ""),
                buyer_country=tender.get("buyer_country", ""),
                value_amount=tender.get("value_amount", 0),
                currency=tender.get("currency", "EUR"),
                url=tender.get("url", "")
            )
            tenders.append(tender_response)
        
        # Apply filters
        filtered_tenders = tenders
        
        if query:
            filtered_tenders = [
                t for t in filtered_tenders 
                if query.lower() in t.title.lower() or query.lower() in t.summary.lower()
            ]
        
        if country:
            filtered_tenders = [
                t for t in filtered_tenders 
                if t.buyer_country.upper() == country.upper()
            ]
        
        if min_value:
            filtered_tenders = [
                t for t in filtered_tenders 
                if t.value_amount >= min_value
            ]
        
        if max_value:
            filtered_tenders = [
                t for t in filtered_tenders 
                if t.value_amount <= max_value
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
        # Get sample data for stats
        tenders = await fetch_last_tenders(200)
        
        countries = {}
        total_value = 0
        sources = {}
        
        for tender in tenders:
            country = tender.get("buyer_country", "Unknown")
            countries[country] = countries.get(country, 0) + 1
            
            value = tender.get("value_amount", 0)
            total_value += value
            
            source = tender.get("source", "Unknown")
            sources[source] = sources.get(source, 0) + 1
        
        return {
            "total_tenders": len(tenders),
            "total_value": total_value,
            "countries": len(countries),
            "country_breakdown": countries,
            "source_breakdown": sources,
            "average_value": total_value // len(tenders) if tenders else 0
        }
        
    except Exception as e:
        return {
            "total_tenders": 0,
            "total_value": 0,
            "countries": 0,
            "country_breakdown": {},
            "source_breakdown": {},
            "average_value": 0
        }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting TenderPulse API...")
    print("📊 API Documentation: http://localhost:8000/docs")
    print("🔍 Tenders Endpoint: http://localhost:8000/api/v1/tenders/tenders")
    print("📈 Stats Endpoint: http://localhost:8000/api/v1/tenders/stats/summary")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
