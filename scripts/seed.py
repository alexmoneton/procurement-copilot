#!/usr/bin/env python3
"""Seed script to populate database with demo data."""

import asyncio
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List

from app.db.session import init_db, close_db, AsyncSessionLocal
from app.db.crud import TenderCRUD, UserCRUD, SavedFilterCRUD, CompanyCRUD, AwardCRUD
from app.db.schemas import TenderCreate, UserCreate, SavedFilterCreate, CompanyCreate, AwardCreate
from app.db.models import TenderSource, NotifyFrequency


async def create_sample_tenders(db) -> List[str]:
    """Create 100 sample tenders."""
    print("Creating sample tenders...")
    
    sample_tenders = [
        {
            "tender_ref": f"TED-2024-{i:03d}",
            "source": TenderSource.TED,
            "title": f"IT Services Contract {i}",
            "summary": f"Comprehensive IT services for government agency {i}",
            "publication_date": date.today() - timedelta(days=i),
            "deadline_date": date.today() + timedelta(days=30-i),
            "cpv_codes": ["72000000", "48000000"],
            "buyer_name": f"Ministry of Digital Affairs {i}",
            "buyer_country": "FR",
            "value_amount": Decimal(f"{100000 + i * 10000}"),
            "currency": "EUR",
            "url": f"https://ted.europa.eu/tender-{i}"
        }
        for i in range(1, 51)
    ]
    
    # Add construction tenders
    construction_tenders = [
        {
            "tender_ref": f"BOAMP-2024-{i:03d}",
            "source": TenderSource.BOAMP,
            "title": f"Construction Project {i}",
            "summary": f"Public construction project for infrastructure {i}",
            "publication_date": date.today() - timedelta(days=i+10),
            "deadline_date": date.today() + timedelta(days=45-i),
            "cpv_codes": ["45000000", "71000000"],
            "buyer_name": f"City Council {i}",
            "buyer_country": "FR",
            "value_amount": Decimal(f"{500000 + i * 50000}"),
            "currency": "EUR",
            "url": f"https://boamp.fr/tender-{i}"
        }
        for i in range(1, 31)
    ]
    
    # Add consulting tenders
    consulting_tenders = [
        {
            "tender_ref": f"TED-2024-CONSULT-{i:03d}",
            "source": TenderSource.TED,
            "title": f"Consulting Services {i}",
            "summary": f"Strategic consulting services for public sector {i}",
            "publication_date": date.today() - timedelta(days=i+20),
            "deadline_date": date.today() + timedelta(days=60-i),
            "cpv_codes": ["79000000", "80000000"],
            "buyer_name": f"Regional Authority {i}",
            "buyer_country": "FR",
            "value_amount": Decimal(f"{200000 + i * 20000}"),
            "currency": "EUR",
            "url": f"https://ted.europa.eu/consulting-{i}"
        }
        for i in range(1, 21)
    ]
    
    all_tenders = sample_tenders + construction_tenders + consulting_tenders
    tender_refs = []
    
    for tender_data in all_tenders:
        tender = TenderCreate(**tender_data)
        db_tender = await TenderCRUD.create(db, tender)
        tender_refs.append(db_tender.tender_ref)
    
    print(f"Created {len(tender_refs)} sample tenders")
    return tender_refs


async def create_demo_user(db) -> str:
    """Create demo user."""
    print("Creating demo user...")
    
    user_data = UserCreate(
        email="demo@procurement-copilot.com",
        full_name="Demo User",
        is_active=True
    )
    
    user = await UserCRUD.create(db, user_data)
    print(f"Created demo user: {user.email}")
    return str(user.id)


async def create_demo_filters(db, user_id: str):
    """Create demo saved filters."""
    print("Creating demo saved filters...")
    
    filters_data = [
        {
            "name": "IT Services - France",
            "keywords": ["software", "development", "IT", "digital"],
            "cpv_codes": ["72000000", "48000000"],
            "countries": ["FR"],
            "min_value": 50000,
            "max_value": 1000000,
            "frequency": NotifyFrequency.DAILY
        },
        {
            "name": "Construction Projects",
            "keywords": ["construction", "building", "infrastructure"],
            "cpv_codes": ["45000000", "71000000"],
            "countries": ["FR", "DE", "ES"],
            "min_value": 100000,
            "max_value": 5000000,
            "frequency": NotifyFrequency.WEEKLY
        },
        {
            "name": "Consulting Services",
            "keywords": ["consulting", "advisory", "strategy"],
            "cpv_codes": ["79000000", "80000000"],
            "countries": ["FR"],
            "min_value": 25000,
            "max_value": 500000,
            "frequency": NotifyFrequency.DAILY
        }
    ]
    
    for filter_data in filters_data:
        filter_data["user_id"] = user_id
        saved_filter = SavedFilterCreate(**filter_data)
        await SavedFilterCRUD.create(db, saved_filter)
    
    print(f"Created {len(filters_data)} demo saved filters")


async def create_sample_companies(db):
    """Create sample companies for outreach."""
    print("Creating sample companies...")
    
    companies_data = [
        {
            "name": "Tech Solutions France",
            "domain": "techsolutions.fr",
            "email": "contact@techsolutions.fr",
            "country": "FR"
        },
        {
            "name": "Digital Innovation GmbH",
            "domain": "digitalinnovation.de",
            "email": "info@digitalinnovation.de",
            "country": "DE"
        },
        {
            "name": "Construction Pro SARL",
            "domain": "constructionpro.fr",
            "email": "contact@constructionpro.fr",
            "country": "FR"
        },
        {
            "name": "Consulting Experts Ltd",
            "domain": "consultingexperts.com",
            "email": "hello@consultingexperts.com",
            "country": "GB"
        },
        {
            "name": "Software Development Co",
            "domain": "softdev.co",
            "email": "contact@softdev.co",
            "country": "FR"
        }
    ]
    
    for company_data in companies_data:
        company = CompanyCreate(**company_data)
        await CompanyCRUD.create(db, company)
    
    print(f"Created {len(companies_data)} sample companies")


async def create_sample_awards(db, tender_refs: List[str]):
    """Create sample awards."""
    print("Creating sample awards...")
    
    # Create awards for some tenders
    for i, tender_ref in enumerate(tender_refs[:20]):  # First 20 tenders
        award_data = AwardCreate(
            tender_ref=tender_ref,
            award_date=date.today() - timedelta(days=i),
            winner_names=[f"Winner Corp {i}"],
            other_bidders=[f"Loser Corp {i}A", f"Loser Corp {i}B"]
        )
        await AwardCRUD.create(db, award_data)
    
    print("Created 20 sample awards")


async def main():
    """Main seeding function."""
    print("Starting database seeding...")
    
    await init_db()
    
    try:
        async with AsyncSessionLocal() as db:
            # Create sample tenders
            tender_refs = await create_sample_tenders(db)
            
            # Create demo user
            user_id = await create_demo_user(db)
            
            # Create demo filters
            await create_demo_filters(db, user_id)
            
            # Create sample companies
            await create_sample_companies(db)
            
            # Create sample awards
            await create_sample_awards(db, tender_refs)
            
            print("Database seeding completed successfully!")
            print(f"Demo user email: demo@procurement-copilot.com")
            print(f"Created {len(tender_refs)} tenders, 1 user, 3 filters, 5 companies, 20 awards")
    
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
