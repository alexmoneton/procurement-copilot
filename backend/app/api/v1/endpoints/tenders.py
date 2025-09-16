"""Tender endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ....db.crud import TenderCRUD
from ....db.schemas import Tender, TenderList, TenderSearchParams, TenderSource
from ....db.session import get_db

router = APIRouter()


@router.get("/tenders", response_model=TenderList)
async def search_tenders(
    query: Optional[str] = Query(None, description="Search query for title and summary"),
    cpv: Optional[str] = Query(None, description="CPV code filter"),
    country: Optional[str] = Query(None, description="Country code filter"),
    from_date: Optional[str] = Query(None, description="From date filter (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="To date filter (YYYY-MM-DD)"),
    min_value: Optional[float] = Query(None, description="Minimum value filter"),
    max_value: Optional[float] = Query(None, description="Maximum value filter"),
    source: Optional[TenderSource] = Query(None, description="Source filter"),
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db),
) -> TenderList:
    """Search tenders with various filters."""
    try:
        # Parse dates
        from datetime import datetime
        
        parsed_from_date = None
        if from_date:
            try:
                parsed_from_date = datetime.strptime(from_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid from_date format. Use YYYY-MM-DD")
        
        parsed_to_date = None
        if to_date:
            try:
                parsed_to_date = datetime.strptime(to_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid to_date format. Use YYYY-MM-DD")
        
        # Convert values to Decimal if provided
        from decimal import Decimal
        
        parsed_min_value = Decimal(str(min_value)) if min_value is not None else None
        parsed_max_value = Decimal(str(max_value)) if max_value is not None else None
        
        # Search tenders
        tenders, total = await TenderCRUD.search(
            db=db,
            query=query,
            cpv=cpv,
            country=country,
            from_date=parsed_from_date,
            to_date=parsed_to_date,
            min_value=parsed_min_value,
            max_value=parsed_max_value,
            source=source,
            limit=limit,
            offset=offset,
        )
        
        # Calculate pagination info
        pages = (total + limit - 1) // limit if total > 0 else 0
        page = (offset // limit) + 1 if offset > 0 else 1
        
        return TenderList(
            items=tenders,
            total=total,
            page=page,
            size=limit,
            pages=pages,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching tenders: {str(e)}")


@router.get("/tenders/{tender_ref}", response_model=Tender)
async def get_tender(
    tender_ref: str,
    db: AsyncSession = Depends(get_db),
) -> Tender:
    """Get a specific tender by reference."""
    tender = await TenderCRUD.get_by_ref(db, tender_ref)
    
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    return tender


@router.get("/tenders/sources/{source}", response_model=TenderList)
async def get_tenders_by_source(
    source: TenderSource,
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db),
) -> TenderList:
    """Get tenders from a specific source."""
    try:
        tenders, total = await TenderCRUD.search(
            db=db,
            source=source,
            limit=limit,
            offset=offset,
        )
        
        # Calculate pagination info
        pages = (total + limit - 1) // limit if total > 0 else 0
        page = (offset // limit) + 1 if offset > 0 else 1
        
        return TenderList(
            items=tenders,
            total=total,
            page=page,
            size=limit,
            pages=pages,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tenders: {str(e)}")


@router.get("/tenders/stats/summary")
async def get_tender_stats(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get tender statistics summary."""
    try:
        from sqlalchemy import func, select
        from ....db.models import Tender, TenderSource
        
        # Total tenders
        total_result = await db.execute(select(func.count(Tender.id)))
        total_tenders = total_result.scalar()
        
        # Tenders by source
        source_result = await db.execute(
            select(Tender.source, func.count(Tender.id))
            .group_by(Tender.source)
        )
        by_source = {row[0].value: row[1] for row in source_result.fetchall()}
        
        # Tenders by country
        country_result = await db.execute(
            select(Tender.buyer_country, func.count(Tender.id))
            .group_by(Tender.buyer_country)
            .order_by(func.count(Tender.id).desc())
            .limit(10)
        )
        by_country = {row[0]: row[1] for row in country_result.fetchall()}
        
        # Recent tenders (last 7 days)
        from datetime import date, timedelta
        week_ago = date.today() - timedelta(days=7)
        recent_result = await db.execute(
            select(func.count(Tender.id))
            .where(Tender.publication_date >= week_ago)
        )
        recent_tenders = recent_result.scalar()
        
        return {
            "total_tenders": total_tenders,
            "by_source": by_source,
            "top_countries": by_country,
            "recent_tenders_7_days": recent_tenders,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching statistics: {str(e)}")
