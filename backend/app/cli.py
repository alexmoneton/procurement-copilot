#!/usr/bin/env python3
"""Command line interface for Procurement Copilot."""

import asyncio
import sys
from typing import Optional

import click
from loguru import logger

from .core.config import settings
from .db.session import init_db, close_db
from .services.ingest import ingest_service
from .services.alerts import alert_service
from .tasks.scheduler import scheduler_manager
from .db.crud import UserCRUD, SavedFilterCRUD, CompanyCRUD
from .db.schemas import UserCreate, SavedFilterCreate, CompanyCreate
from .db.models import NotifyFrequency
from .services.outreach_engine import outreach_engine
from .services.company_resolution import company_resolution_service


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug mode")
def cli(debug: bool):
    """Procurement Copilot CLI."""
    if debug:
        settings.debug = True
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8000, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def serve(host: str, port: int, reload: bool):
    """Start the FastAPI server."""
    import uvicorn
    
    uvicorn.run(
        "backend.app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="debug" if settings.debug else "info",
    )


@cli.command()
@click.option("--ted-limit", default=200, help="Limit for TED tenders")
@click.option("--boamp-limit", default=200, help="Limit for BOAMP tenders")
def ingest(ted_limit: int, boamp_limit: int):
    """Run tender ingestion."""
    async def _ingest():
        await init_db()
        try:
            from .db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                results = await ingest_service.run_ingest(db, ted_limit, boamp_limit)
                click.echo(f"Ingestion completed: {results}")
        finally:
            await close_db()
    
    asyncio.run(_ingest())


@cli.command()
@click.option("--source", type=click.Choice(["TED", "BOAMP_FR"]), help="Source to ingest from")
@click.option("--limit", default=200, help="Limit for tenders")
def ingest_source(source: str, limit: int):
    """Run ingestion from a specific source."""
    async def _ingest_source():
        await init_db()
        try:
            from .db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                results = await ingest_service.ingest_single_source(db, source, limit)
                click.echo(f"Ingestion from {source} completed: {results}")
        finally:
            await close_db()
    
    asyncio.run(_ingest_source())


@cli.command()
def scheduler():
    """Start the scheduler."""
    async def _scheduler():
        await init_db()
        try:
            scheduler_manager.start()
            click.echo("Scheduler started. Press Ctrl+C to stop.")
            
            # Keep running
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            click.echo("Stopping scheduler...")
        finally:
            scheduler_manager.stop()
            await close_db()
    
    asyncio.run(_scheduler())


@cli.command()
def migrate():
    """Run database migrations."""
    import subprocess
    import os
    
    os.chdir("backend/app")
    subprocess.run(["alembic", "upgrade", "head"], check=True)
    click.echo("Migrations completed")


@cli.command()
@click.argument("message")
def migrate_create(message: str):
    """Create a new migration."""
    import subprocess
    import os
    
    os.chdir("backend/app")
    subprocess.run(["alembic", "revision", "--autogenerate", "-m", message], check=True)
    click.echo(f"Migration created: {message}")


@cli.command()
def test():
    """Run tests."""
    import subprocess
    
    subprocess.run(["pytest", "backend/app/tests/", "-v"], check=True)


@cli.command()
def lint():
    """Run linting."""
    import subprocess
    
    subprocess.run(["ruff", "check", "backend/app/"], check=True)
    subprocess.run(["mypy", "backend/app/"], check=True)


@cli.command()
def format_code():
    """Format code."""
    import subprocess
    
    subprocess.run(["ruff", "format", "backend/app/"], check=True)
    subprocess.run(["isort", "backend/app/"], check=True)


# User management commands
@cli.group()
def users():
    """User management commands."""
    pass


@users.command("create")
@click.option("--email", required=True, help="User email address")
def create_user(email: str):
    """Create a new user."""
    async def _create_user():
        await init_db()
        try:
            from .db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                # Check if user already exists
                existing_user = await UserCRUD.get_by_email(db, email)
                if existing_user:
                    click.echo(f"User with email {email} already exists")
                    return
                
                # Create new user
                user_create = UserCreate(email=email)
                user = await UserCRUD.create(db, user_create)
                click.echo(f"User created successfully: {user.email} (ID: {user.id})")
        finally:
            await close_db()
    
    asyncio.run(_create_user())


@users.command("list")
def list_users():
    """List all users."""
    async def _list_users():
        await init_db()
        try:
            from .db.session import AsyncSessionLocal
            from sqlalchemy import select
            from .db.models import User
            
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(User).order_by(User.created_at.desc()))
                users = result.scalars().all()
                
                if not users:
                    click.echo("No users found")
                    return
                
                click.echo(f"Found {len(users)} users:")
                for user in users:
                    click.echo(f"  {user.email} (ID: {user.id}) - Created: {user.created_at}")
        finally:
            await close_db()
    
    asyncio.run(_list_users())


# Filter management commands
@cli.group()
def filters():
    """Filter management commands."""
    pass


@filters.command("create")
@click.option("--email", required=True, help="User email address")
@click.option("--name", required=True, help="Filter name")
@click.option("--keywords", help="Comma-separated keywords")
@click.option("--cpv", help="Comma-separated CPV codes")
@click.option("--countries", help="Comma-separated country codes")
@click.option("--frequency", type=click.Choice(["daily", "weekly"]), default="daily", help="Notification frequency")
@click.option("--min", type=float, help="Minimum value")
@click.option("--max", type=float, help="Maximum value")
def create_filter(email: str, name: str, keywords: str, cpv: str, countries: str, 
                  frequency: str, min: float, max: float):
    """Create a new saved filter for a user."""
    async def _create_filter():
        await init_db()
        try:
            from .db.session import AsyncSessionLocal
            from decimal import Decimal
            
            async with AsyncSessionLocal() as db:
                # Find user
                user = await UserCRUD.get_by_email(db, email)
                if not user:
                    click.echo(f"User with email {email} not found")
                    return
                
                # Parse parameters
                keyword_list = [k.strip() for k in keywords.split(",")] if keywords else []
                cpv_list = [c.strip() for c in cpv.split(",")] if cpv else []
                country_list = [c.strip().upper() for c in countries.split(",")] if countries else []
                
                # Create filter
                filter_data = SavedFilterCreate(
                    name=name,
                    keywords=keyword_list,
                    cpv_codes=cpv_list,
                    countries=country_list,
                    notify_frequency=NotifyFrequency(frequency),
                    min_value=Decimal(str(min)) if min is not None else None,
                    max_value=Decimal(str(max)) if max is not None else None,
                )
                
                saved_filter = await SavedFilterCRUD.create(db, filter_data, user.id)
                click.echo(f"Filter created successfully: {saved_filter.name} (ID: {saved_filter.id})")
        finally:
            await close_db()
    
    asyncio.run(_create_filter())


@filters.command("list")
@click.option("--email", help="Filter by user email")
def list_filters(email: str):
    """List saved filters."""
    async def _list_filters():
        await init_db()
        try:
            from .db.session import AsyncSessionLocal
            from sqlalchemy import select
            from .db.models import SavedFilter, User
            
            async with AsyncSessionLocal() as db:
                if email:
                    # Find user and their filters
                    user = await UserCRUD.get_by_email(db, email)
                    if not user:
                        click.echo(f"User with email {email} not found")
                        return
                    
                    filters = await SavedFilterCRUD.get_by_user(db, user.id)
                    click.echo(f"Filters for {email}:")
                else:
                    # List all filters
                    result = await db.execute(
                        select(SavedFilter, User.email)
                        .join(User)
                        .order_by(SavedFilter.created_at.desc())
                    )
                    filter_data = result.all()
                    
                    if not filter_data:
                        click.echo("No filters found")
                        return
                    
                    click.echo(f"Found {len(filter_data)} filters:")
                    for saved_filter, user_email in filter_data:
                        click.echo(f"  {saved_filter.name} (ID: {saved_filter.id})")
                        click.echo(f"    User: {user_email}")
                        click.echo(f"    Keywords: {', '.join(saved_filter.keywords) if saved_filter.keywords else 'None'}")
                        click.echo(f"    CPV: {', '.join(saved_filter.cpv_codes) if saved_filter.cpv_codes else 'None'}")
                        click.echo(f"    Countries: {', '.join(saved_filter.countries) if saved_filter.countries else 'None'}")
                        click.echo(f"    Frequency: {saved_filter.notify_frequency.value}")
                        click.echo(f"    Created: {saved_filter.created_at}")
                        click.echo()
                    return
                
                if not filters:
                    click.echo(f"No filters found for {email}")
                    return
                
                for saved_filter in filters:
                    click.echo(f"  {saved_filter.name} (ID: {saved_filter.id})")
                    click.echo(f"    Keywords: {', '.join(saved_filter.keywords) if saved_filter.keywords else 'None'}")
                    click.echo(f"    CPV: {', '.join(saved_filter.cpv_codes) if saved_filter.cpv_codes else 'None'}")
                    click.echo(f"    Countries: {', '.join(saved_filter.countries) if saved_filter.countries else 'None'}")
                    click.echo(f"    Frequency: {saved_filter.notify_frequency.value}")
                    click.echo(f"    Created: {saved_filter.created_at}")
                    click.echo()
        finally:
            await close_db()
    
    asyncio.run(_list_filters())


# Alert commands
@cli.group()
def alerts():
    """Alert management commands."""
    pass


@alerts.command("send")
def send_alerts():
    """Send alerts for all daily filters."""
    async def _send_alerts():
        await init_db()
        try:
            from .db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                results = await alert_service.run_alerts_pipeline(db)
                click.echo(f"Alerts sent: {results['emails_sent']}")
                click.echo(f"Alerts skipped: {results['emails_skipped']}")
                click.echo(f"Errors: {results['errors']}")
        finally:
            await close_db()
    
    asyncio.run(_send_alerts())


@alerts.command("send-filter")
@click.option("--filter-id", required=True, help="Filter ID to send alerts for")
def send_filter_alerts(filter_id: str):
    """Send alerts for a specific filter."""
    async def _send_filter_alerts():
        await init_db()
        try:
            from .db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                result = await alert_service.send_alerts_for_filter(db, filter_id)
                click.echo(f"Filter alert result: {result}")
        finally:
            await close_db()
    
    asyncio.run(_send_filter_alerts())


@cli.group()
def leads():
    """Lead generation and outreach commands."""
    pass


@leads.command("build")
@click.option("--strategy", required=True, type=click.Choice(["lost_bidders", "cross_border", "lapsed"]), help="Targeting strategy")
@click.option("--cpv", help="CPV codes (comma-separated)")
@click.option("--country", help="Country code (e.g., FR, DE)")
@click.option("--limit", type=int, default=200, help="Maximum number of leads")
def build_leads(strategy: str, cpv: str, country: str, limit: int):
    """Build a lead list based on targeting strategy."""
    
    async def _build_leads():
        await init_db()
        try:
            from .db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                # Parse CPV codes
                cpv_codes = None
                if cpv:
                    cpv_codes = [c.strip() for c in cpv.split(",") if c.strip()]
                
                # Build lead list
                leads = await outreach_engine.build_lead_list(
                    db, strategy, cpv_codes, country, limit
                )
                
                click.echo(f"Built {len(leads)} leads using strategy: {strategy}")
                click.echo(f"CPV codes: {cpv_codes or 'All'}")
                click.echo(f"Country: {country or 'All'}")
                click.echo(f"Limit: {limit}")
                click.echo("")
                
                # Display first 10 leads
                for i, lead in enumerate(leads[:10]):
                    click.echo(f"{i+1}. {lead.get('name', 'Unknown')}")
                    if 'bid_count' in lead:
                        click.echo(f"   Bid count: {lead['bid_count']}")
                    if 'strong_country' in lead:
                        click.echo(f"   Strong country: {lead['strong_country']}")
                    if 'active_bid_count' in lead:
                        click.echo(f"   Active bid count: {lead['active_bid_count']}")
                    click.echo("")
                
                if len(leads) > 10:
                    click.echo(f"... and {len(leads) - 10} more leads")
                
        finally:
            await close_db()
    
    asyncio.run(_build_leads())


@leads.command("send")
@click.option("--campaign", required=True, type=click.Choice(["missed_opportunities", "cross_border_expansion", "reactivation"]), help="Campaign type")
@click.option("--strategy", required=True, type=click.Choice(["lost_bidders", "cross_border", "lapsed"]), help="Targeting strategy")
@click.option("--cpv", help="CPV codes (comma-separated)")
@click.option("--country", help="Country code (e.g., FR, DE)")
@click.option("--limit", type=int, default=50, help="Maximum number of emails to send")
def send_campaign(campaign: str, strategy: str, cpv: str, country: str, limit: int):
    """Send outreach campaign to leads."""
    
    async def _send_campaign():
        await init_db()
        try:
            from .db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                # Parse CPV codes
                cpv_codes = None
                if cpv:
                    cpv_codes = [c.strip() for c in cpv.split(",") if c.strip()]
                
                # Build lead list
                click.echo(f"Building lead list with strategy: {strategy}")
                leads = await outreach_engine.build_lead_list(
                    db, strategy, cpv_codes, country, limit * 2  # Get more leads than we'll send
                )
                
                if not leads:
                    click.echo("No leads found for the specified criteria")
                    return
                
                click.echo(f"Found {len(leads)} leads")
                
                # Send campaign
                click.echo(f"Sending {campaign} campaign to {min(len(leads), limit)} leads...")
                results = await outreach_engine.send_campaign(
                    db, campaign, leads, cpv_codes, country, limit
                )
                
                # Display results
                click.echo("")
                click.echo("Campaign Results:")
                click.echo(f"  Total leads: {results['total_leads']}")
                click.echo(f"  Emails sent: {results['sent']}")
                click.echo(f"  Failed: {results['failed']}")
                click.echo(f"  Skipped: {results['skipped']}")
                
                if results['errors']:
                    click.echo("")
                    click.echo("Errors:")
                    for error in results['errors'][:5]:  # Show first 5 errors
                        click.echo(f"  - {error}")
                    if len(results['errors']) > 5:
                        click.echo(f"  ... and {len(results['errors']) - 5} more errors")
                
        finally:
            await close_db()
    
    asyncio.run(_send_campaign())


@cli.group()
def companies():
    """Company management commands."""
    pass


@companies.command("import")
@click.option("--file", required=True, help="CSV file path")
@click.option("--has-header", is_flag=True, default=True, help="CSV has header row")
def import_companies(file: str, has_header: bool):
    """Import companies from CSV file."""
    
    async def _import_companies():
        await init_db()
        try:
            from .db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                # Read CSV file
                with open(file, 'r', encoding='utf-8') as f:
                    csv_content = f.read()
                
                # Import companies
                results = await company_resolution_service.import_companies_from_csv(
                    db, csv_content, has_header
                )
                
                # Display results
                click.echo("Import Results:")
                click.echo(f"  Imported: {results['imported']}")
                click.echo(f"  Updated: {results['updated']}")
                click.echo(f"  Errors: {results['errors']}")
                
                if results['error_details']:
                    click.echo("")
                    click.echo("Error Details:")
                    for error in results['error_details'][:10]:  # Show first 10 errors
                        click.echo(f"  - {error}")
                    if len(results['error_details']) > 10:
                        click.echo(f"  ... and {len(results['error_details']) - 10} more errors")
                
        finally:
            await close_db()
    
    asyncio.run(_import_companies())


@companies.command("list")
@click.option("--country", help="Filter by country code")
@click.option("--limit", type=int, default=50, help="Maximum number of companies to show")
def list_companies(country: str, limit: int):
    """List companies in the database."""
    
    async def _list_companies():
        await init_db()
        try:
            from .db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                if country:
                    companies = await CompanyCRUD.get_companies_by_country(db, country, limit)
                else:
                    companies = await CompanyCRUD.get_active_companies(db, limit)
                
                click.echo(f"Found {len(companies)} companies")
                click.echo("")
                
                for i, company in enumerate(companies):
                    click.echo(f"{i+1}. {company.name}")
                    click.echo(f"   Country: {company.country}")
                    if company.domain:
                        click.echo(f"   Domain: {company.domain}")
                    if company.email:
                        click.echo(f"   Email: {company.email}")
                    click.echo(f"   Suppressed: {company.is_suppressed}")
                    if company.last_contacted:
                        click.echo(f"   Last contacted: {company.last_contacted}")
                    click.echo("")
                
        finally:
            await close_db()
    
    asyncio.run(_list_companies())


if __name__ == "__main__":
    cli()
