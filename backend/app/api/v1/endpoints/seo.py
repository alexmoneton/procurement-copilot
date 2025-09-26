"""SEO endpoints for programmatic SEO system."""

import asyncio
import json
import os
from datetime import datetime
from typing import List, Optional

import openai
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.config import settings
from ....db.crud import TenderCRUD
from ....db.session import get_db

router = APIRouter()

# Initialize OpenAI
openai.api_key = getattr(settings, "openai_api_key", os.getenv("OPENAI_API_KEY"))

# Load massive SEO dataset
_seo_tenders_cache = None

def load_massive_seo_data():
    """Load the massive SEO dataset."""
    global _seo_tenders_cache
    
    if _seo_tenders_cache is None:
        try:
            # Try to load the massive dataset first
            with open('massive_seo_tenders.json', 'r') as f:
                _seo_tenders_cache = json.load(f)
        except FileNotFoundError:
            # Fallback to empty list if file doesn't exist
            _seo_tenders_cache = []
    
    return _seo_tenders_cache


class TenderSEO(BaseModel):
    id: str
    title: str
    country: str
    category: str
    year: int
    budget_band: str
    deadline: str
    url: str
    value_amount: Optional[float] = None
    currency: Optional[str] = None
    cpv_codes: Optional[List[str]] = None
    buyer_name: Optional[str] = None
    buyer_country: Optional[str] = None
    source: Optional[str] = None
    summary: Optional[str] = None


class PageIntro(BaseModel):
    country: str
    category: str
    year: int
    budget: str
    intro_text: str


class SitemapData(BaseModel):
    country: str
    category: str
    year: int
    budget: str
    tender_count: int
    total_value: Optional[float] = None


@router.get("/tenders", response_model=List[TenderSEO])
async def get_tenders_seo(
    country: Optional[str] = Query(None, description="Filter by country"),
    category: Optional[str] = Query(None, description="Filter by category"),
    year: Optional[int] = Query(None, description="Filter by year"),
    budget: Optional[str] = Query(None, description="Filter by budget band"),
    limit: int = Query(50, le=100, description="Number of results to return"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get tenders filtered by country, category, year, and budget band for SEO pages.
    """
    try:
        # Load massive SEO dataset
        massive_tenders = load_massive_seo_data()
        
        if massive_tenders:
            # Filter the massive dataset
            filtered_tenders = []
            for tender_data in massive_tenders:
                # Apply filters
                if country and tender_data.get('country') != country:
                    continue
                if category and tender_data.get('category') != category:
                    continue
                if year and tender_data.get('year') != year:
                    continue
                if budget and tender_data.get('budget_band') != budget:
                    continue
                
                filtered_tenders.append(TenderSEO(**tender_data))
                
                # Limit results
                if len(filtered_tenders) >= limit:
                    break
            
            return filtered_tenders
        
        # Fallback to database if massive dataset not available
        tenders, total = await TenderCRUD.search(
            db=db, country=country, limit=limit, offset=0
        )

        # Convert to SEO format
        seo_tenders = []
        for tender in tenders:
            # Map categories based on CPV codes or other logic
            category = (
                _map_cpv_to_category(tender.cpv_codes)
                if tender.cpv_codes
                else "General"
            )
            budget_band = (
                _map_value_to_budget_band(tender.value_amount)
                if tender.value_amount
                else "Unknown"
            )
            year = (
                tender.publication_date.year
                if tender.publication_date
                else datetime.now().year
            )

            seo_tenders.append(
                TenderSEO(
                    id=str(tender.id),
                    title=tender.title,
                    country=tender.buyer_country or "Unknown",
                    category=category,
                    year=year,
                    budget_band=budget_band,
                    deadline=(
                        tender.deadline_date.isoformat() if tender.deadline_date else ""
                    ),
                    url=tender.url,
                    value_amount=(
                        float(tender.value_amount) if tender.value_amount else None
                    ),
                    currency=tender.currency,
                    cpv_codes=tender.cpv_codes,
                    buyer_name=tender.buyer_name,
                    buyer_country=tender.buyer_country,
                    source=tender.source.value if tender.source else None,
                    summary=tender.summary,
                )
            )

        return seo_tenders

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tenders: {str(e)}")


@router.get("/page-intro", response_model=PageIntro)
async def get_or_create_page_intro(
    country: str = Query(..., description="Country code"),
    category: str = Query(..., description="Category name"),
    year: int = Query(..., description="Year"),
    budget: str = Query(..., description="Budget band"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get cached page intro or generate new one with GPT.
    """
    try:
        # For now, generate intro directly (in production, you'd cache this)
        intro_text = await _generate_page_intro(country, category, year, budget)

        return PageIntro(
            country=country,
            category=category,
            year=year,
            budget=budget,
            intro_text=intro_text,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating page intro: {str(e)}"
        )


@router.get("/sitemap-data", response_model=List[SitemapData])
async def get_sitemap_data(db: AsyncSession = Depends(get_db)):
    """
    Get all unique combinations for sitemap generation.
    """
    try:
        # Get all tenders
        tenders, total = await TenderCRUD.search(db=db, limit=1000)

        # Group by combinations
        combinations = {}
        for tender in tenders:
            category = (
                _map_cpv_to_category(tender.cpv_codes)
                if tender.cpv_codes
                else "General"
            )
            budget_band = (
                _map_value_to_budget_band(tender.value_amount)
                if tender.value_amount
                else "Unknown"
            )
            year = (
                tender.publication_date.year
                if tender.publication_date
                else datetime.now().year
            )
            country = tender.buyer_country or "Unknown"

            key = (country, category, year, budget_band)
            if key not in combinations:
                combinations[key] = {
                    "country": country,
                    "category": category,
                    "year": year,
                    "budget": budget_band,
                    "tender_count": 0,
                    "total_value": 0,
                }

            combinations[key]["tender_count"] += 1
            if tender.value_amount:
                combinations[key]["total_value"] += float(tender.value_amount)

        return [
            SitemapData(
                country=combo["country"],
                category=combo["category"],
                year=combo["year"],
                budget=combo["budget"],
                tender_count=combo["tender_count"],
                total_value=combo["total_value"],
            )
            for combo in combinations.values()
        ]

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating sitemap data: {str(e)}"
        )


@router.get("/stats/country/{country}")
async def get_country_stats(country: str, db: AsyncSession = Depends(get_db)):
    """Get statistics for a specific country."""
    try:
        tenders, total = await TenderCRUD.search(db=db, country=country, limit=1000)

        if not tenders:
            raise HTTPException(
                status_code=404, detail="No tenders found for this country"
            )

        # Calculate statistics
        total_value = sum(float(t.value_amount) for t in tenders if t.value_amount)
        categories = set()
        years = set()

        for tender in tenders:
            if tender.cpv_codes:
                categories.add(_map_cpv_to_category(tender.cpv_codes))
            if tender.publication_date:
                years.add(tender.publication_date.year)

        return {
            "country": country,
            "total_tenders": total,
            "total_value": total_value,
            "categories": list(categories),
            "years": list(years),
            "avg_value": total_value / total if total > 0 else 0,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching country stats: {str(e)}"
        )


@router.get("/stats/category/{category}")
async def get_category_stats(category: str, db: AsyncSession = Depends(get_db)):
    """Get statistics for a specific category."""
    try:
        # This would need to be implemented based on your category mapping logic
        # For now, return a placeholder
        return {
            "category": category,
            "total_tenders": 0,
            "total_value": 0,
            "countries": [],
            "years": [],
            "avg_value": 0,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching category stats: {str(e)}"
        )


# Helper functions
def _map_cpv_to_category(cpv_codes: List[str]) -> str:
    """Map CPV codes to categories."""
    if not cpv_codes:
        return "General"

    # Map first CPV code to category
    cpv = cpv_codes[0]

    category_mapping = {
        "72000000": "Information Technology",
        "79400000": "Consulting",
        "60100000": "Transportation",
        "34600000": "Automotive",
        "45000000": "Construction",
        "48000000": "Software",
        "71000000": "Engineering",
        "73000000": "Research & Development",
        "75000000": "Public Administration",
        "80000000": "Education",
        "85000000": "Healthcare",
        "90000000": "Environmental",
    }

    return category_mapping.get(cpv, "General")


def _map_value_to_budget_band(value: float) -> str:
    """Map tender value to budget band."""
    if value is None:
        return "Unknown"

    if value < 50000:
        return "€0-€50K"
    elif value < 500000:
        return "€50K-€500K"
    elif value < 2000000:
        return "€500K-€2M"
    elif value < 10000000:
        return "€2M-€10M"
    else:
        return "€10M+"


async def _generate_page_intro(
    country: str, category: str, year: int, budget: str
) -> str:
    """Generate page intro using OpenAI."""
    try:
        if not openai.api_key:
            # Fallback intro if OpenAI is not configured
            return f"Discover {category} tenders in {country} for {year} within the {budget} budget range. Find the latest government procurement opportunities updated daily."

        prompt = f"""You are writing short, SEO-friendly intro blurbs for a government tender directory.

Page context:
- Country: {country}
- Category: {category}
- Year: {year}
- Budget band: {budget}

Instructions:
- Write a 2–3 sentence introduction for this tender listing page.
- Be clear, professional, and informative.
- Mention the country, category, and year naturally.
- Emphasize that these are the latest opportunities, updated regularly.
- Add a light variation in tone so not all blurbs are identical.
- Avoid generic filler like "Welcome to our page."
- Maximum length: 60 words.

Now generate the intro."""

        response = await asyncio.to_thread(
            openai.ChatCompletion.create,
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        # Fallback intro if GPT fails
        return f"Explore {category} tenders in {country} for {year} within the {budget} budget range. These opportunities are updated daily to ensure you have access to the latest government procurement contracts."
