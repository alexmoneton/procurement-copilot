#!/usr/bin/env python3

"""
Minimal TenderPulse API for Railway deployment
"""

import os
import random
import uuid
from datetime import datetime, date, timedelta
from typing import List, Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Pydantic models
class TenderResponse(BaseModel):
    id: str
    tender_ref: str
    title: str
    summary: Optional[str]
    publication_date: str
    deadline_date: Optional[str]
    cpv_codes: List[str]
    buyer_name: str
    buyer_country: str
    value_amount: str
    currency: str
    url: str
    source: str

class TendersListResponse(BaseModel):
    items: List[TenderResponse]
    total: int
    page: int
    size: int
    pages: int

# Create FastAPI app
app = FastAPI(
    title="TenderPulse API",
    description="Real-time signals for public contracts",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def generate_tenders(limit: int = 20) -> List[dict]:
    """Generate realistic tender data."""
    countries = ['SPAIN', 'GERMANY', 'FRANCE', 'ITALY', 'NETHERLANDS', 'UK', 'POLAND', 'SWEDEN']
    country_codes = {'SPAIN': 'ES', 'GERMANY': 'DE', 'FRANCE': 'FR', 'ITALY': 'IT', 
                    'NETHERLANDS': 'NL', 'UK': 'GB', 'POLAND': 'PL', 'SWEDEN': 'SE'}
    
    sectors = [
        ("IT Services", ["72000000", "79400000"]),
        ("Construction", ["45000000", "71000000"]),
        ("Healthcare", ["33000000", "85000000"]),
        ("Transport", ["60100000", "34600000"]),
        ("Energy", ["09000000", "31600000"]),
        ("Education", ["80000000", "92000000"])
    ]
    
    tenders = []
    base_date = datetime.now().date()
    
    for i in range(limit):
        country = random.choice(countries)
        sector, cpv_codes = random.choice(sectors)
        
        tender = {
            'id': str(uuid.uuid4()),
            'tender_ref': f"{country_codes[country]}-{random.randint(2025100001, 2025100999)}",
            'source': country,
            'title': f"{sector} - Procurement {i+1}",
            'summary': f"Public procurement for {sector.lower()} in {country.title()}.",
            'publication_date': (base_date - timedelta(days=random.randint(0, 5))).isoformat(),
            'deadline_date': (base_date + timedelta(days=random.randint(15, 45))).isoformat(),
            'cpv_codes': cpv_codes,
            'buyer_name': f"Ministry of {sector} - {country.title()}",
            'buyer_country': country_codes[country],
            'value_amount': str(random.randint(100000, 2000000)),
            'currency': 'EUR',
            'url': f"https://procurement.{country_codes[country].lower()}/tender/{random.randint(2025100001, 2025100999)}"
        }
        tenders.append(tender)
    
    return tenders

@app.get("/")
async def root():
    return {
        "message": "TenderPulse API",
        "description": "Real-time signals for public contracts",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/ping")
async def ping():
    """Railway healthcheck endpoint."""
    return {"status": "ok", "message": "pong"}

@app.get("/api/v1/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/v1/tenders/tenders", response_model=TendersListResponse)
async def get_tenders(
    limit: int = Query(default=20, ge=1, le=100),
    page: int = Query(default=1, ge=1),
    query: Optional[str] = Query(default=None),
    country: Optional[str] = Query(default=None),
    min_value: Optional[int] = Query(default=None),
    max_value: Optional[int] = Query(default=None)
):
    """Get procurement tenders with filtering and pagination."""
    # Generate tenders
    raw_tenders = generate_tenders(200)  # Generate full dataset
    
    # Filter tenders
    filtered_tenders = raw_tenders
    
    if query:
        filtered_tenders = [t for t in filtered_tenders if query.lower() in t['title'].lower()]
    
    if country:
        filtered_tenders = [t for t in filtered_tenders if t['buyer_country'].lower() == country.lower()]
    
    if min_value:
        filtered_tenders = [t for t in filtered_tenders if int(t['value_amount']) >= min_value]
    
    if max_value:
        filtered_tenders = [t for t in filtered_tenders if int(t['value_amount']) <= max_value]
    
    # Pagination
    total = len(filtered_tenders)
    start = (page - 1) * limit
    end = start + limit
    page_tenders = filtered_tenders[start:end]
    
    # Convert to response format
    tender_responses = []
    for tender in page_tenders:
        tender_response = TenderResponse(
            id=tender['id'],
            tender_ref=tender['tender_ref'],
            title=tender['title'],
            summary=tender['summary'],
            publication_date=tender['publication_date'],
            deadline_date=tender['deadline_date'],
            cpv_codes=tender['cpv_codes'],
            buyer_name=tender['buyer_name'],
            buyer_country=tender['buyer_country'],
            value_amount=tender['value_amount'],
            currency=tender['currency'],
            url=tender['url'],
            source=tender['source']
        )
        tender_responses.append(tender_response)
    
    return TendersListResponse(
        items=tender_responses,
        total=total,
        page=page,
        size=len(tender_responses),
        pages=(total + limit - 1) // limit
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Starting TenderPulse API on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
