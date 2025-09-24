"""CRUD operations for database models."""

import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Tender, User, SavedFilter, EmailLog, Award, Company, TenderSource, UserProfile
from .schemas import TenderCreate, TenderUpdate, UserCreate, SavedFilterCreate, SavedFilterUpdate, EmailLogCreate, AwardCreate, CompanyCreate, CompanyUpdate, UserProfileCreate, UserProfileUpdate


class TenderCRUD:
    """CRUD operations for Tender model."""
    
    @staticmethod
    async def create(db: AsyncSession, tender: TenderCreate) -> Tender:
        """Create a new tender."""
        db_tender = Tender(**tender.model_dump())
        db.add(db_tender)
        await db.commit()
        await db.refresh(db_tender)
        return db_tender
    
    @staticmethod
    async def get_by_id(db: AsyncSession, tender_id: uuid.UUID) -> Optional[Tender]:
        """Get tender by ID."""
        result = await db.execute(select(Tender).where(Tender.id == tender_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_ref(db: AsyncSession, tender_ref: str) -> Optional[Tender]:
        """Get tender by reference."""
        result = await db.execute(select(Tender).where(Tender.tender_ref == tender_ref))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update(
        db: AsyncSession, 
        tender_id: uuid.UUID, 
        tender_update: TenderUpdate
    ) -> Optional[Tender]:
        """Update tender."""
        result = await db.execute(select(Tender).where(Tender.id == tender_id))
        db_tender = result.scalar_one_or_none()
        
        if not db_tender:
            return None
        
        update_data = tender_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_tender, field, value)
        
        await db.commit()
        await db.refresh(db_tender)
        return db_tender
    
    @staticmethod
    async def delete(db: AsyncSession, tender_id: uuid.UUID) -> bool:
        """Delete tender."""
        result = await db.execute(select(Tender).where(Tender.id == tender_id))
        db_tender = result.scalar_one_or_none()
        
        if not db_tender:
            return False
        
        await db.delete(db_tender)
        await db.commit()
        return True
    
    @staticmethod
    async def search(
        db: AsyncSession,
        query: Optional[str] = None,
        cpv: Optional[str] = None,
        country: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        min_value: Optional[Decimal] = None,
        max_value: Optional[Decimal] = None,
        source: Optional[TenderSource] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Tender], int]:
        """Search tenders with filters."""
        # Base query
        stmt = select(Tender)
        count_stmt = select(func.count(Tender.id))
        
        # Apply filters
        conditions = []
        
        if query:
            search_term = f"%{query.lower()}%"
            conditions.append(
                or_(
                    func.lower(Tender.title).like(search_term),
                    func.lower(Tender.summary).like(search_term),
                )
            )
        
        if cpv:
            conditions.append(Tender.cpv_codes.contains([cpv]))
        
        if country:
            conditions.append(Tender.buyer_country == country.upper())
        
        if from_date:
            conditions.append(Tender.publication_date >= from_date)
        
        if to_date:
            conditions.append(Tender.publication_date <= to_date)
        
        if min_value is not None:
            conditions.append(Tender.value_amount >= min_value)
        
        if max_value is not None:
            conditions.append(Tender.value_amount <= max_value)
        
        if source:
            conditions.append(Tender.source == source)
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
            count_stmt = count_stmt.where(and_(*conditions))
        
        # Order by publication date descending
        stmt = stmt.order_by(desc(Tender.publication_date))
        
        # Apply pagination
        stmt = stmt.offset(offset).limit(limit)
        
        # Execute queries
        result = await db.execute(stmt)
        tenders = result.scalars().all()
        
        count_result = await db.execute(count_stmt)
        total = count_result.scalar()
        
        return list(tenders), total
    
    @staticmethod
    async def upsert_by_ref(db: AsyncSession, tender: TenderCreate) -> Tender:
        """Upsert tender by reference (insert or update)."""
        existing = await TenderCRUD.get_by_ref(db, tender.tender_ref)
        
        if existing:
            # Update existing tender
            update_data = tender.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(existing, field, value)
            await db.commit()
            await db.refresh(existing)
            return existing
        else:
            # Create new tender
            return await TenderCRUD.create(db, tender)


class UserCRUD:
    """CRUD operations for User model."""
    
    @staticmethod
    async def create(db: AsyncSession, user: UserCreate) -> User:
        """Create a new user."""
        db_user = User(**user.model_dump())
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
    
    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()


class SavedFilterCRUD:
    """CRUD operations for SavedFilter model."""
    
    @staticmethod
    async def create(db: AsyncSession, filter_data: SavedFilterCreate, user_id: uuid.UUID) -> SavedFilter:
        """Create a new saved filter."""
        db_filter = SavedFilter(**filter_data.model_dump(), user_id=user_id)
        db.add(db_filter)
        await db.commit()
        await db.refresh(db_filter)
        return db_filter
    
    @staticmethod
    async def get_by_id(db: AsyncSession, filter_id: uuid.UUID) -> Optional[SavedFilter]:
        """Get saved filter by ID."""
        result = await db.execute(select(SavedFilter).where(SavedFilter.id == filter_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_user(db: AsyncSession, user_id: uuid.UUID) -> list[SavedFilter]:
        """Get all saved filters for a user."""
        result = await db.execute(
            select(SavedFilter)
            .where(SavedFilter.user_id == user_id)
            .order_by(desc(SavedFilter.created_at))
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_daily_filters(db: AsyncSession) -> list[SavedFilter]:
        """Get all saved filters with daily notification frequency."""
        from .models import NotifyFrequency
        
        result = await db.execute(
            select(SavedFilter)
            .where(SavedFilter.notify_frequency == NotifyFrequency.DAILY)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def update(
        db: AsyncSession, 
        filter_id: uuid.UUID, 
        filter_update: SavedFilterUpdate
    ) -> Optional[SavedFilter]:
        """Update saved filter."""
        result = await db.execute(select(SavedFilter).where(SavedFilter.id == filter_id))
        db_filter = result.scalar_one_or_none()
        
        if not db_filter:
            return None
        
        update_data = filter_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_filter, field, value)
        
        await db.commit()
        await db.refresh(db_filter)
        return db_filter
    
    @staticmethod
    async def delete(db: AsyncSession, filter_id: uuid.UUID) -> bool:
        """Delete saved filter."""
        result = await db.execute(select(SavedFilter).where(SavedFilter.id == filter_id))
        db_filter = result.scalar_one_or_none()
        
        if not db_filter:
            return False
        
        await db.delete(db_filter)
        await db.commit()
        return True


class EmailLogCRUD:
    """CRUD operations for EmailLog model."""
    
    @staticmethod
    async def create(db: AsyncSession, email_log: EmailLogCreate) -> EmailLog:
        """Create a new email log entry."""
        db_email_log = EmailLog(**email_log.model_dump())
        db.add(db_email_log)
        await db.commit()
        await db.refresh(db_email_log)
        return db_email_log
    
    @staticmethod
    async def get_by_id(db: AsyncSession, email_log_id: uuid.UUID) -> Optional[EmailLog]:
        """Get email log by ID."""
        result = await db.execute(select(EmailLog).where(EmailLog.id == email_log_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_user(db: AsyncSession, user_id: uuid.UUID, limit: int = 50) -> list[EmailLog]:
        """Get email logs for a user."""
        result = await db.execute(
            select(EmailLog)
            .where(EmailLog.user_id == user_id)
            .order_by(desc(EmailLog.sent_at))
            .limit(limit)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_by_filter(db: AsyncSession, filter_id: uuid.UUID, limit: int = 50) -> list[EmailLog]:
        """Get email logs for a saved filter."""
        result = await db.execute(
            select(EmailLog)
            .where(EmailLog.saved_filter_id == filter_id)
            .order_by(desc(EmailLog.sent_at))
            .limit(limit)
        )
        return list(result.scalars().all())


class AwardCRUD:
    """CRUD operations for Award model."""
    
    @staticmethod
    async def create(db: AsyncSession, award: AwardCreate) -> Award:
        """Create a new award."""
        db_award = Award(**award.model_dump())
        db.add(db_award)
        await db.commit()
        await db.refresh(db_award)
        return db_award
    
    @staticmethod
    async def get_by_id(db: AsyncSession, award_id: uuid.UUID) -> Optional[Award]:
        """Get award by ID."""
        result = await db.execute(select(Award).where(Award.id == award_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_tender_ref(db: AsyncSession, tender_ref: str) -> Optional[Award]:
        """Get award by tender reference."""
        result = await db.execute(select(Award).where(Award.tender_ref == tender_ref))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_recent_awards(db: AsyncSession, limit: int = 100) -> list[Award]:
        """Get recent awards ordered by award date."""
        result = await db.execute(
            select(Award)
            .order_by(desc(Award.award_date))
            .limit(limit)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_awards_by_date_range(
        db: AsyncSession, 
        start_date: date, 
        end_date: date
    ) -> list[Award]:
        """Get awards within date range."""
        result = await db.execute(
            select(Award)
            .where(and_(
                Award.award_date >= start_date,
                Award.award_date <= end_date
            ))
            .order_by(desc(Award.award_date))
        )
        return list(result.scalars().all())


class CompanyCRUD:
    """CRUD operations for Company model."""
    
    @staticmethod
    async def create(db: AsyncSession, company: CompanyCreate) -> Company:
        """Create a new company."""
        db_company = Company(**company.model_dump())
        db.add(db_company)
        await db.commit()
        await db.refresh(db_company)
        return db_company
    
    @staticmethod
    async def get_by_id(db: AsyncSession, company_id: uuid.UUID) -> Optional[Company]:
        """Get company by ID."""
        result = await db.execute(select(Company).where(Company.id == company_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_name_and_country(
        db: AsyncSession, 
        name: str, 
        country: str
    ) -> Optional[Company]:
        """Get company by name and country."""
        result = await db.execute(
            select(Company).where(
                and_(
                    func.lower(Company.name) == name.lower(),
                    Company.country == country.upper()
                )
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_domain(db: AsyncSession, domain: str) -> Optional[Company]:
        """Get company by domain."""
        result = await db.execute(
            select(Company).where(func.lower(Company.domain) == domain.lower())
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[Company]:
        """Get company by email."""
        result = await db.execute(
            select(Company).where(func.lower(Company.email) == email.lower())
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_active_companies(db: AsyncSession, limit: int = 100) -> list[Company]:
        """Get active companies (not suppressed)."""
        result = await db.execute(
            select(Company)
            .where(Company.is_suppressed == False)
            .order_by(desc(Company.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_companies_by_country(
        db: AsyncSession, 
        country: str, 
        limit: int = 100
    ) -> list[Company]:
        """Get companies by country."""
        result = await db.execute(
            select(Company)
            .where(Company.country == country.upper())
            .order_by(desc(Company.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def update(
        db: AsyncSession, 
        company_id: uuid.UUID, 
        company_update: CompanyUpdate
    ) -> Optional[Company]:
        """Update a company."""
        result = await db.execute(select(Company).where(Company.id == company_id))
        db_company = result.scalar_one_or_none()
        
        if not db_company:
            return None
        
        update_data = company_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_company, field, value)
        
        await db.commit()
        await db.refresh(db_company)
        return db_company
    
    @staticmethod
    async def upsert_by_name_and_country(
        db: AsyncSession, 
        company: CompanyCreate
    ) -> Company:
        """Upsert company by name and country."""
        existing = await CompanyCRUD.get_by_name_and_country(
            db, company.name, company.country
        )
        
        if existing:
            # Update existing company
            update_data = CompanyUpdate(**company.model_dump())
            return await CompanyCRUD.update(db, existing.id, update_data)
        else:
            # Create new company
            return await CompanyCRUD.create(db, company)
    
    @staticmethod
    async def suppress_company(db: AsyncSession, company_id: uuid.UUID) -> bool:
        """Add company to suppression list."""
        result = await db.execute(select(Company).where(Company.id == company_id))
        db_company = result.scalar_one_or_none()
        
        if not db_company:
            return False
        
        db_company.is_suppressed = True
        await db.commit()
        return True
    
    @staticmethod
    async def update_last_contacted(
        db: AsyncSession, 
        company_id: uuid.UUID
    ) -> bool:
        """Update last contacted timestamp."""
        result = await db.execute(select(Company).where(Company.id == company_id))
        db_company = result.scalar_one_or_none()
        
        if not db_company:
            return False
        
        from datetime import datetime
        db_company.last_contacted = datetime.now()
        await db.commit()
        return True


class UserProfileCRUD:
    """CRUD operations for UserProfile model."""
    
    @staticmethod
    async def create(db: AsyncSession, user_id: uuid.UUID, profile: UserProfileCreate) -> UserProfile:
        """Create a new user profile."""
        db_profile = UserProfile(user_id=user_id, **profile.model_dump())
        db.add(db_profile)
        await db.commit()
        await db.refresh(db_profile)
        return db_profile
    
    @staticmethod
    async def get_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[UserProfile]:
        """Get user profile by user ID."""
        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update(
        db: AsyncSession, 
        user_id: uuid.UUID, 
        profile_update: UserProfileUpdate
    ) -> Optional[UserProfile]:
        """Update user profile."""
        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        db_profile = result.scalar_one_or_none()
        
        if not db_profile:
            return None
        
        update_data = profile_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_profile, field, value)
        
        await db.commit()
        await db.refresh(db_profile)
        return db_profile
    
    @staticmethod
    async def upsert(
        db: AsyncSession, 
        user_id: uuid.UUID, 
        profile: UserProfileCreate
    ) -> UserProfile:
        """Create or update user profile."""
        existing = await UserProfileCRUD.get_by_user_id(db, user_id)
        
        if existing:
            # Update existing profile
            update_data = UserProfileUpdate(**profile.model_dump())
            return await UserProfileCRUD.update(db, user_id, update_data)
        else:
            # Create new profile
            return await UserProfileCRUD.create(db, user_id, profile)
    
    @staticmethod
    async def delete(db: AsyncSession, user_id: uuid.UUID) -> bool:
        """Delete user profile."""
        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        db_profile = result.scalar_one_or_none()
        
        if not db_profile:
            return False
        
        await db.delete(db_profile)
        await db.commit()
        return True
