# Procurement Copilot

AI-powered procurement tender monitoring system that automatically scrapes, processes, and provides search capabilities for public procurement opportunities from TED (Tenders Electronic Daily) and BOAMP France.

## Features

- **Automated Scraping**: Regularly scrapes tender data from TED and BOAMP France
- **Smart Deduplication**: Removes duplicate tenders using advanced similarity algorithms
- **CPV Mapping**: Maps tender content to CPV (Common Procurement Vocabulary) codes
- **RESTful API**: FastAPI-based API with comprehensive search and filtering
- **Scheduled Jobs**: Automated data ingestion every 6 hours
- **Email Alerts**: Daily email notifications for matching tenders
- **Outreach Engine**: Targeted outreach to SME bidders based on public tender data
- **Lead Generation**: Identify active but losing, cross-border potential, and lapsed bidders
- **Email Campaigns**: Personalized outreach with missed opportunities and upcoming tenders
- **Company Resolution**: Enrich supplier data with domains and contact information
- **User Management**: CLI tools for user and filter management
- **Docker Support**: Full containerization with docker-compose
- **Comprehensive Testing**: Full test suite with pytest

## Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.x, Alembic
- **Database**: PostgreSQL with async support
- **Queue/Scheduler**: APScheduler for background jobs
- **Email**: Resend API for transactional emails
- **Scraping**: httpx, selectolax, playwright (for complex portals)
- **Testing**: pytest, pytest-asyncio
- **Code Quality**: ruff, mypy, pre-commit

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- Make (optional, for convenience commands)

### One-Liner Development Setup

```bash
make up
```

This starts all services with Docker Compose. The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/api/v1/docs

### 1. Clone and Setup

```bash
git clone <repository-url>
cd procurement-copilot
make env-setup  # Copy environment file
# Edit .env with your settings
```

### 2. Start Services

```bash
make up  # Start all services with docker-compose
```

### 3. Initialize Database

```bash
make migrate  # Run database migrations
```

### 4. Run Initial Data Ingestion

```bash
make ingest  # Scrape and ingest initial tender data
```

### 5. Configure Email Alerts (Optional)

```bash
# Edit .env file and add your Resend API key
echo "RESEND_API_KEY=your-resend-api-key-here" >> .env

# Create a test user
python -m backend.app.cli users create --email test@example.com

# Create a sample filter
python -m backend.app.cli filters create \
  --email test@example.com \
  --name "IT Services France" \
  --keywords "IT,software" \
  --cpv "72000000,30200000" \
  --countries "FR" \
  --frequency daily \
  --min 20000
```

### 6. Set Up Frontend (Optional)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Copy environment template
cp env.example .env.local

# Edit .env.local with your API keys:
# - Clerk authentication keys
# - Stripe payment keys  
# - Backend API URL (http://localhost:8000)

# Start development server
npm run dev
```

### 7. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/v1/docs
- **Health Check**: http://localhost:8000/api/v1/health

## Frontend Application

The frontend is a modern Next.js 14 application with the following features:

### Features

- **Modern UI**: Built with Next.js 14, TypeScript, and Tailwind CSS
- **Authentication**: Clerk integration with email magic link
- **Payments**: Stripe integration for subscription billing
- **Real-time Dashboard**: Live tender feed with filtering and search
- **Saved Filters**: Create and manage custom tender filters
- **Responsive Design**: Mobile-first design with beautiful UI components

### Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Authentication**: Clerk
- **Payments**: Stripe
- **Icons**: Heroicons, Lucide React
- **UI Components**: Headless UI

### Configuration

#### Clerk Setup
1. Create account at [clerk.com](https://clerk.com)
2. Create new application
3. Enable email magic link authentication
4. Get API keys from dashboard
5. Add to `.env.local`

#### Stripe Setup
1. Create account at [stripe.com](https://stripe.com)
2. Get API keys from dashboard
3. Create products and prices for plans
4. Set up webhooks for subscription events
5. Add keys to `.env.local`

#### Environment Variables
```env
# Clerk Authentication
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...

# Stripe
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Testing Payments

Use these Stripe test cards:
- **Success**: `4242 4242 4242 4242`
- **Decline**: `4000 0000 0000 0002`
- **3D Secure**: `4000 0025 0000 3155`

## Outreach Engine

The outreach engine uses public tender data to create highly relevant outreach campaigns to SME bidders.

### Features

- **Target Selection**: Three sophisticated targeting strategies
- **Email Templates**: Personalized campaigns with actual tender data
- **Company Resolution**: Enrich supplier data with contact information
- **Rate Limiting**: Compliance with email best practices
- **Suppression Lists**: Respect unsubscribe requests

### Targeting Strategies

#### 1. Active but Losing SMEs
Companies that appear in `other_bidders` ≥ 2 times in the last 6 months.

```bash
# Build lead list
python -m backend.app.cli leads build --strategy lost_bidders --cpv 72000000 --country FR --limit 200

# Send campaign
python -m backend.app.cli leads send --campaign missed_opportunities --strategy lost_bidders --limit 50
```

#### 2. Cross-Border Potential
Companies with ≥ 3 bids in one country and zero in neighbors, for same CPV family.

```bash
# Build lead list
python -m backend.app.cli leads build --strategy cross_border --cpv 72000000 --limit 200

# Send campaign
python -m backend.app.cli leads send --campaign cross_border_expansion --strategy cross_border --limit 50
```

#### 3. Lapsed Bidders
Companies that bid frequently 12-6 months ago, but 6-0 months show zero activity.

```bash
# Build lead list
python -m backend.app.cli leads build --strategy lapsed --cpv 72000000 --country FR --limit 200

# Send campaign
python -m backend.app.cli leads send --campaign reactivation --strategy lapsed --limit 50
```

### Email Campaigns

#### Missed Opportunities
- **Subject**: "You missed 3 tenders in {sector} last month"
- **Content**: Lists recent missed tenders and upcoming opportunities
- **CTA**: Free trial signup

#### Cross-Border Expansion
- **Subject**: "You're strong in {home_country}. Here's what you're missing in {adjacent_country}"
- **Content**: Upcoming tenders in neighboring countries
- **CTA**: Start monitoring neighboring country tenders

#### Reactivation
- **Subject**: "Are you still bidding in {sector}? Here's a curated list for this month"
- **Content**: Curated list of relevant upcoming tenders
- **CTA**: Get back in the game

### Company Management

#### Import Companies from CSV
```bash
# Create CSV with columns: name, domain, email, country
python -m backend.app.cli companies import --file companies.csv
```

#### List Companies
```bash
# List all companies
python -m backend.app.cli companies list

# Filter by country
python -m backend.app.cli companies list --country FR --limit 50
```

### Makefile Commands

```bash
# Lead generation
make leads-build STRATEGY=lost_bidders CPV=72000000 COUNTRY=FR LIMIT=200
make leads-send CAMPAIGN=missed_opportunities STRATEGY=lost_bidders LIMIT=50

# Company management
make companies-import FILE=companies.csv
make companies-list COUNTRY=FR LIMIT=50
```

### Safety & Compliance

- **Value-First**: All emails provide actual tender data and opportunities
- **Unsubscribe Links**: Every email includes unsubscribe functionality
- **Rate Limiting**: Maximum 50 emails per hour with delays
- **Suppression Lists**: Companies can be added to suppression lists
- **Contact Frequency**: No more than once per week per company

### Database Schema

#### Awards Table
Stores awarded tender information with winner and loser data:
- `tender_ref`: Reference to the awarded tender
- `award_date`: Date when the award was made
- `winner_names`: Array of winning supplier names
- `other_bidders`: Array of other bidder names (if available)

#### Companies Table
Stores supplier information:
- `name`: Company name
- `domain`: Company website domain
- `email`: Primary contact email
- `country`: Company country code
- `is_suppressed`: Whether company is on suppression list
- `last_contacted`: Last outreach timestamp

## Deployment

### Development (Docker Compose)

```bash
# Start all services
make up

# View logs
make logs

# Stop services
make down

# Seed database with demo data
make db-seed

# Generate demo data for marketing
make demo-data
```

### Production Deployment

#### Option 1: Single VPS with Docker

```bash
# Clone repository
git clone <repository-url>
cd procurement-copilot

# Copy environment file
cp infra/env.example infra/.env
# Edit infra/.env with production values

# Start production services
make deploy

# Run migrations
make db-migrate

# Seed initial data
make db-seed
```

#### Option 2: Railway + Vercel (Recommended)

**Backend (Railway):**
1. Connect GitHub repository to Railway
2. Set environment variables in Railway dashboard
3. Deploy automatically on push to main

**Frontend (Vercel):**
1. Connect GitHub repository to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy automatically on push to main

**Database:**
- Use Railway PostgreSQL addon
- Or external managed PostgreSQL (AWS RDS, DigitalOcean, etc.)

#### Option 3: Render + Vercel

**Backend (Render):**
1. Create new Web Service on Render
2. Connect GitHub repository
3. Set build command: `pip install -e .`
4. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add PostgreSQL database

**Frontend (Vercel):**
1. Connect GitHub repository to Vercel
2. Set environment variables
3. Deploy automatically

### Environment Variables

Copy `infra/env.example` to `infra/.env` and configure:

```bash
# Required for production
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
RESEND_API_KEY=re_your_production_key
STRIPE_SECRET_KEY=sk_live_your_live_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_your_live_key
CLERK_SECRET_KEY=sk_live_your_live_key

# Optional
SENTRY_DSN=your_sentry_dsn
GRAFANA_PASSWORD=secure_password
```

### Monitoring & Logging

```bash
# Start monitoring stack (Grafana + Loki)
make monitoring-up

# Access Grafana at http://localhost:3001
# Default login: admin / admin (change password)
```

### Backups

```bash
# Create database backup
make db-backup

# Backups are stored in ./backups/ directory
# For production, configure S3 upload in backup script
```

### SSL/HTTPS

For production, ensure SSL certificates are configured:

- **Vercel**: Automatic SSL
- **Railway**: Automatic SSL
- **VPS**: Use Let's Encrypt with nginx reverse proxy

### Scaling

**Horizontal Scaling:**
- Use load balancer (nginx, Cloudflare)
- Multiple API instances
- Redis for session storage
- CDN for static assets

**Vertical Scaling:**
- Increase container resources in docker-compose.prod.yml
- Use managed databases with read replicas
- Implement caching strategies

## Development

### Local Development Setup

```bash
# Install dependencies
make dev-install

# Start database only
cd infra && docker-compose up -d postgres redis

# Run migrations
make migrate

# Start development server
make dev

# Run tests
make test

# Run linting
make lint

# Format code
make format
```

### Available Make Commands

```bash
make help  # Show all available commands

# Docker
make up          # Start all services
make down        # Stop all services
make logs        # Show logs
make status      # Show service status

# Database
make migrate     # Run migrations
make migrate-create MESSAGE="description"  # Create new migration
make db-shell    # Connect to database shell
make db-reset    # Reset database (WARNING: destroys data)

# Data
make ingest      # Run tender ingestion
make ingest-ted  # Run TED ingestion only
make ingest-boamp # Run BOAMP ingestion only

# Development
make dev         # Start development server
make scheduler   # Start scheduler standalone
make test        # Run tests
make test-cov    # Run tests with coverage
make lint        # Run linting
make format      # Format code

# Cleanup
make clean       # Clean temporary files
make clean-docker # Clean Docker resources
```

## API Endpoints

### Health Check
- `GET /api/v1/health` - Service health status

### Tenders
- `GET /api/v1/tenders` - Search tenders with filters
- `GET /api/v1/tenders/{tender_ref}` - Get specific tender
- `GET /api/v1/tenders/sources/{source}` - Get tenders by source
- `GET /api/v1/tenders/stats/summary` - Get tender statistics

### Search Parameters
- `query` - Text search in title/summary
- `cpv` - Filter by CPV code
- `country` - Filter by country code
- `from_date` / `to_date` - Date range filter
- `min_value` / `max_value` - Value range filter
- `source` - Filter by source (TED, BOAMP_FR)
- `limit` / `offset` - Pagination

### Example API Calls

```bash
# Search for software tenders in France
curl "http://localhost:8000/api/v1/tenders?query=software&country=FR&limit=10"

# Get tenders from TED source
curl "http://localhost:8000/api/v1/tenders/sources/TED"

# Get tender statistics
curl "http://localhost:8000/api/v1/tenders/stats/summary"
```

## Database Schema

### Tenders Table
- `id` - UUID primary key
- `tender_ref` - Unique tender reference
- `source` - Source (TED, BOAMP_FR)
- `title` - Tender title
- `summary` - Tender description
- `publication_date` - Publication date
- `deadline_date` - Submission deadline
- `cpv_codes` - Array of CPV codes
- `buyer_name` - Buying organization
- `buyer_country` - Country code
- `value_amount` - Estimated value
- `currency` - Currency code
- `url` - Original tender URL
- `created_at` / `updated_at` - Timestamps

### Users Table
- `id` - UUID primary key
- `email` - User email
- `created_at` - Registration timestamp

### Saved Filters Table
- `id` - UUID primary key
- `user_id` - Foreign key to users
- `keywords` - Search keywords
- `cpv_codes` - CPV code filters
- `countries` - Country filters
- `min_value` / `max_value` - Value range
- `notify_frequency` - Notification frequency
- `created_at` / `updated_at` - Timestamps

## Scrapers

### TED Scraper
- Uses data.europa.eu CSV API
- Fetches latest tender data
- Handles rate limiting and retries
- Robust field parsing and validation

### BOAMP France Scraper
- Scrapes boamp.fr website
- Uses selectolax for HTML parsing
- Fallback to playwright for complex pages
- Extracts tender details and metadata

## Services

### Ingestion Service
- Orchestrates data collection from all sources
- Normalizes and validates tender data
- Handles deduplication
- Upserts data to database

### CPV Mapping Service
- Maps tender content to CPV codes
- Keyword-based suggestions
- Hierarchical CPV code support
- Validation and normalization

### Deduplication Service
- Advanced similarity algorithms
- Multi-field comparison (title, buyer, CPV, value)
- Configurable similarity thresholds
- Quality-based selection

## Background Jobs

### Scheduled Jobs
- **Ingestion Job**: Runs every 6 hours
- **Alerts Job**: Runs daily at 7:30 AM (sends email notifications)
- **Cleanup Job**: Runs daily at 2 AM (removes old tenders)

### Manual Jobs
```bash
# Run ingestion manually
python -m backend.app.tasks.jobs run_ingest

# Run specific source ingestion
python -m backend.app.tasks.jobs run_ted_ingest
python -m backend.app.tasks.jobs run_boamp_ingest

# Run cleanup
python -m backend.app.tasks.jobs cleanup

# Send alerts
python -m backend.app.tasks.jobs send_alerts
python -m backend.app.tasks.jobs send_alerts_filter <filter-id>
```

## Email Alerts System

The system includes a comprehensive email alerts system that automatically notifies users about new tenders matching their saved filters.

### Features

- **Daily Notifications**: Automatically sends email digests at 7:30 AM Europe/Paris
- **Smart Matching**: Matches tenders based on keywords, CPV codes, countries, and value ranges
- **HTML & Text Emails**: Beautiful HTML emails with fallback text versions
- **Deduplication**: Prevents duplicate notifications for the same tender
- **Email Logging**: Tracks all sent emails for audit purposes

### Alert Selection Logic

For each saved filter with daily frequency, the system:

1. **Date Filter**: Selects tenders published in the last 24 hours
2. **Keyword Matching**: Uses ILIKE search on title and summary for any keywords
3. **CPV Overlap**: Matches tenders with overlapping CPV codes
4. **Country Overlap**: Matches tenders from specified countries
5. **Value Range**: Filters by min/max value if specified
6. **Deduplication**: Removes duplicates by tender reference
7. **Skip Logic**: Skips email if no matching tenders found

### Email Format

**Subject**: `[Procurement Copilot] New tenders for: {filter.name} ({count})`

**Content**:
- Professional HTML design with company branding
- For each tender: title (linked), buyer, country, deadline, CPV codes, estimated value
- Footer with manage alerts and unsubscribe links
- Text version for email clients that don't support HTML

### User Management

```bash
# Create a user
python -m backend.app.cli users create --email user@example.com

# List all users
python -m backend.app.cli users list

# Create a saved filter
python -m backend.app.cli filters create \
  --email user@example.com \
  --name "IT Services France" \
  --keywords "IT,software,development" \
  --cpv "72000000,30200000" \
  --countries "FR,DE" \
  --frequency daily \
  --min 20000 \
  --max 500000

# List filters
python -m backend.app.cli filters list
python -m backend.app.cli filters list --email user@example.com
```

### Alert Management

```bash
# Send alerts for all daily filters
python -m backend.app.cli alerts send

# Send alerts for a specific filter
python -m backend.app.cli alerts send-filter --filter-id <uuid>

# Using Makefile
make alerts
make alerts-filter FILTER_ID=<uuid>
```

### Resend Configuration

1. **Sign up** at [resend.com](https://resend.com)
2. **Get API key** from your dashboard
3. **Add to environment**:
   ```bash
   echo "RESEND_API_KEY=re_your_api_key_here" >> .env
   ```
4. **Restart services**:
   ```bash
   make down && make up
   ```

### Testing Alerts

```bash
# Create test user and filter
python -m backend.app.cli users create --email test@example.com
python -m backend.app.cli filters create \
  --email test@example.com \
  --name "Test Filter" \
  --keywords "test" \
  --frequency daily

# Run initial data ingestion
make ingest

# Send test alerts
make alerts
```

## Configuration

Environment variables (see `infra/env.example`):

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=procurement_copilot
DB_USER=postgres
DB_PASSWORD=postgres

# Scraping
SCRAPING_REQUEST_TIMEOUT=30
SCRAPING_MAX_RETRIES=3
SCRAPING_RATE_LIMIT_DELAY=0.5

# Email
RESEND_API_KEY=your-resend-api-key-here

# Scheduler
INGEST_INTERVAL_HOURS=6
SCHEDULER_TIMEZONE=Europe/Paris
```

## Testing

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
pytest backend/app/tests/test_scrapers.py -v

# Run with watch mode
make test-watch
```

## Monitoring

### Logs
- Application logs: `logs/error.log`
- Docker logs: `make logs`
- Service-specific logs: `make logs-api`, `make logs-scheduler`

### Health Checks
- API health: `curl http://localhost:8000/api/v1/health`
- Service status: `make status`

## Production Deployment

1. **Environment Setup**
   ```bash
   cp infra/env.example .env
   # Edit .env with production values
   ```

2. **Build and Deploy**
   ```bash
   make build
   # Deploy using your preferred method
   ```

3. **Database Migration**
   ```bash
   make migrate
   ```

4. **Initial Data Load**
   ```bash
   make ingest
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make test`
5. Run linting: `make lint`
6. Submit a pull request

## License

[Add your license here]

## Support

For issues and questions:
- Create an issue in the repository
- Check the documentation at `/api/v1/docs`
- Review logs for debugging information
