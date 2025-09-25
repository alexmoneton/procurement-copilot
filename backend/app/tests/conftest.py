"""Pytest configuration and fixtures."""

import asyncio
from datetime import date, datetime
from decimal import Decimal
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from app.core.config import settings
from app.db.base import Base
from app.db.models import (NotifyFrequency, SavedFilter, Tender, TenderSource,
                           User)
from app.db.session import get_db
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.pool import StaticPool

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    # Create test engine
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        yield session

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def test_tender_data() -> dict:
    """Sample tender data for testing."""
    return {
        "tender_ref": "TEST-2024-001",
        "source": TenderSource.TED,
        "title": "Test Tender for Software Development",
        "summary": "This is a test tender for software development services",
        "publication_date": date(2024, 1, 15),
        "deadline_date": date(2024, 2, 15),
        "cpv_codes": ["48000000", "72000000"],
        "buyer_name": "Test Organization",
        "buyer_country": "FR",
        "value_amount": Decimal("100000.00"),
        "currency": "EUR",
        "url": "https://example.com/tender/test-2024-001",
    }


@pytest_asyncio.fixture
async def test_user_data() -> dict:
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
    }


@pytest_asyncio.fixture
async def test_saved_filter_data() -> dict:
    """Sample saved filter data for testing."""
    return {
        "name": "Test Filter",
        "keywords": ["software", "development"],
        "cpv_codes": ["48000000", "72000000"],
        "countries": ["FR", "DE"],
        "min_value": Decimal("50000.00"),
        "max_value": Decimal("500000.00"),
        "notify_frequency": NotifyFrequency.DAILY,
    }


@pytest_asyncio.fixture
async def sample_tenders(test_db: AsyncSession) -> list[Tender]:
    """Create sample tenders in the test database."""
    tenders = []

    # Create multiple test tenders
    for i in range(5):
        tender = Tender(
            tender_ref=f"TEST-2024-{i+1:03d}",
            source=TenderSource.TED if i % 2 == 0 else TenderSource.BOAMP_FR,
            title=f"Test Tender {i+1}",
            summary=f"This is test tender {i+1}",
            publication_date=date(2024, 1, 15 + i),
            deadline_date=date(2024, 2, 15 + i),
            cpv_codes=[f"4800000{i}", f"7200000{i}"],
            buyer_name=f"Test Organization {i+1}",
            buyer_country="FR" if i % 2 == 0 else "DE",
            value_amount=Decimal(f"{100000 + i * 10000}.00"),
            currency="EUR",
            url=f"https://example.com/tender/test-2024-{i+1:03d}",
        )
        test_db.add(tender)
        tenders.append(tender)

    await test_db.commit()

    for tender in tenders:
        await test_db.refresh(tender)

    return tenders


@pytest_asyncio.fixture
async def sample_user(test_db: AsyncSession) -> User:
    """Create a sample user in the test database."""
    user = User(email="test@example.com")
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture
async def sample_saved_filter(test_db: AsyncSession, sample_user: User) -> SavedFilter:
    """Create a sample saved filter in the test database."""
    saved_filter = SavedFilter(
        user_id=sample_user.id,
        name="Sample Filter",
        keywords=["software", "development"],
        cpv_codes=["48000000", "72000000"],
        countries=["FR", "DE"],
        min_value=Decimal("50000.00"),
        max_value=Decimal("500000.00"),
        notify_frequency=NotifyFrequency.DAILY,
    )
    test_db.add(saved_filter)
    await test_db.commit()
    await test_db.refresh(saved_filter)
    return saved_filter


@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for testing scrapers."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "Mock response text"
    mock_response.json.return_value = {"mock": "data"}
    mock_response.raise_for_status.return_value = None
    mock_client.get.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_csv_content():
    """Mock CSV content for TED scraper testing."""
    return """TED_CN,TITLE,DATE_PUB,DEADLINE,CPV,BUYER_NAME,COUNTRY,VALUE,CURRENCY,URL,SUMMARY
TEST-001,Test Tender 1,2024-01-15,2024-02-15,48000000,Test Org 1,FR,100000,EUR,https://example.com/1,Test summary 1
TEST-002,Test Tender 2,2024-01-16,2024-02-16,72000000,Test Org 2,DE,200000,EUR,https://example.com/2,Test summary 2"""


@pytest.fixture
def mock_html_content():
    """Mock HTML content for BOAMP scraper testing."""
    return """
    <html>
        <body>
            <article class="avis">
                <h2><a href="/avis/12345">Test BOAMP Tender</a></h2>
                <div class="date">15/01/2024</div>
                <div class="buyer">Test BOAMP Organization</div>
                <div class="value">150000 €</div>
            </article>
        </body>
    </html>
    """


@pytest.fixture
def override_get_db(test_db: AsyncSession):
    """Override the get_db dependency for testing."""

    async def _override_get_db():
        yield test_db

    return _override_get_db
