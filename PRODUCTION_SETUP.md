# TenderPulse Production Setup Guide

## 🚀 Complete Deployment Guide

### Prerequisites
- Domain: `tenderpulse.eu` and `api.tenderpulse.eu`
- Stripe account (live mode)
- Resend account with verified domain
- Clerk account (production)
- Railway/Render account
- Vercel account

---

## 🔧 1. Stripe Live Mode Setup

### Create Products & Prices
```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login to Stripe
stripe login

# Create products (run once)
stripe products create \
  --name "TenderPulse Starter" \
  --description "1 saved filter, daily alerts"

stripe prices create \
  --unit-amount 9900 \
  --currency eur \
  --recurring interval=month \
  --product prod_STARTER_ID

stripe products create \
  --name "TenderPulse Pro" \
  --description "5 saved filters, daily alerts, priority support"

stripe prices create \
  --unit-amount 19900 \
  --currency eur \
  --recurring interval=month \
  --product prod_PRO_ID

stripe products create \
  --name "TenderPulse Team" \
  --description "15 saved filters, daily alerts, team management"

stripe prices create \
  --unit-amount 39900 \
  --currency eur \
  --recurring interval=month \
  --product prod_TEAM_ID
```

### Configure Webhook
```bash
# Create webhook endpoint
stripe webhook_endpoints create \
  --url https://api.tenderpulse.eu/api/v1/billing/webhook \
  --enabled-events customer.subscription.created \
  --enabled-events customer.subscription.updated \
  --enabled-events customer.subscription.deleted \
  --enabled-events invoice.payment_succeeded \
  --enabled-events invoice.payment_failed

# Test webhook locally during development
stripe listen --forward-to localhost:8000/api/v1/billing/webhook
```

### Environment Variables
```bash
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
NEXT_PUBLIC_STRIPE_PRICE_IDS={"starter":"price_...","pro":"price_...","team":"price_..."}
```

---

## 📧 2. Resend Production Setup

### Domain Setup
1. **Add Domain**: `mail.tenderpulse.eu` in Resend dashboard
2. **DNS Records**:
```dns
# SPF Record
mail.tenderpulse.eu TXT "v=spf1 include:_spf.resend.com ~all"

# DKIM Record (from Resend dashboard)
resend._domainkey.mail.tenderpulse.eu CNAME resend.com

# DMARC Record
_dmarc.mail.tenderpulse.eu TXT "v=DMARC1; p=quarantine; rua=mailto:dmarc@tenderpulse.eu"

# MX Record (optional, for receiving emails)
mail.tenderpulse.eu MX 10 feedback-smtp.eu-west-1.amazonses.com
```

3. **Verify Domain**: Wait for DNS propagation (up to 48 hours)

### Email Configuration
```bash
RESEND_API_KEY=re_live_...
EMAIL_FROM=alerts@mail.tenderpulse.eu
EMAIL_FROM_NAME=TenderPulse Alerts
SUPPORT_EMAIL=support@tenderpulse.eu
```

### Domain Warmup (Important!)
```bash
# Week 1: 50 emails/day
# Week 2: 100 emails/day  
# Week 3: 200 emails/day
# Week 4+: Normal volume

# Monitor reputation in Resend dashboard
# Keep bounce rate < 2%
# Keep complaint rate < 0.1%
```

---

## 🔐 3. Clerk Production Setup

### Create Production Instance
1. Go to Clerk dashboard
2. Create new application: "TenderPulse Production"
3. Configure sign-in methods: Email (magic link)
4. Set up custom domain: `auth.tenderpulse.eu` (optional)

### Environment Variables
```bash
CLERK_SECRET_KEY=sk_live_...
CLERK_PUBLISHABLE_KEY=pk_live_...
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...

# Frontend configuration
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/app
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/app
```

---

## 🗄️ 4. Database Deployment (Railway)

### Option A: Railway Deployment
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and create project
railway login
railway new
railway add --database postgresql

# Deploy database first
railway up --service postgresql

# Get database URL
railway variables --service postgresql
# Copy DATABASE_URL for API deployment
```

### Option B: Render Deployment
```yaml
# Use render.yaml configuration
# Database will be created automatically
# Daily backups included in Starter plan
```

### Database Configuration
```bash
DATABASE_URL=postgresql://username:password@hostname:5432/tenderpulse_prod
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Enable SSL
DATABASE_URL=postgresql://username:password@hostname:5432/tenderpulse_prod?sslmode=require
```

---

## 🔧 5. API Deployment

### Railway Deployment
```bash
# Connect to Railway project
railway link

# Set environment variables
railway variables set ENVIRONMENT=production
railway variables set ENABLE_CONNECTORS=TED
railway variables set TZ=Europe/Paris
railway variables set DATABASE_URL=$DATABASE_URL
railway variables set RESEND_API_KEY=$RESEND_API_KEY
railway variables set STRIPE_SECRET_KEY=$STRIPE_SECRET_KEY
railway variables set STRIPE_WEBHOOK_SECRET=$STRIPE_WEBHOOK_SECRET
railway variables set CLERK_SECRET_KEY=$CLERK_SECRET_KEY
railway variables set BACKEND_BASE_URL=https://api.tenderpulse.eu
railway variables set FRONTEND_BASE_URL=https://tenderpulse.eu

# Deploy API
railway up

# Run migrations
railway run python -m alembic upgrade head

# Set custom domain
railway domain add api.tenderpulse.eu
```

### Render Deployment
```bash
# Push code to GitHub
git push origin main

# Connect repository in Render dashboard
# Use render.yaml for configuration
# Set environment variables in dashboard
# Custom domain: api.tenderpulse.eu
```

### Post-Deployment Verification
```bash
# Test API health
curl https://api.tenderpulse.eu/api/v1/health

# Test data ingestion
curl https://api.tenderpulse.eu/api/v1/tenders?limit=5

# Test webhook endpoint
curl -X POST https://api.tenderpulse.eu/api/v1/billing/webhook \
  -H "Content-Type: application/json" \
  -d '{"type": "ping"}'
```

---

## 🌐 6. Frontend Deployment (Vercel)

### Domain Setup
```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Link project
cd frontend
vercel link

# Set production domain
vercel domains add tenderpulse.eu
```

### Environment Variables
```bash
# Set via Vercel dashboard or CLI
vercel env add NEXT_PUBLIC_BACKEND_URL production
# Enter: https://api.tenderpulse.eu

vercel env add NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY production
# Enter: pk_live_...

vercel env add CLERK_SECRET_KEY production
# Enter: sk_live_...

vercel env add NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY production
# Enter: pk_live_...

vercel env add NEXT_PUBLIC_STRIPE_PRICE_IDS production
# Enter: {"starter":"price_...","pro":"price_...","team":"price_..."}
```

### Deploy to Production
```bash
# Deploy to production
vercel --prod

# Verify deployment
curl https://tenderpulse.eu
curl https://tenderpulse.eu/api/health
```

---

## 🔍 7. Monitoring Setup

### UptimeRobot Configuration
```bash
# API Health Check
URL: https://api.tenderpulse.eu/api/v1/health
Method: GET
Interval: 5 minutes
Timeout: 30 seconds
Alert Contacts: alexandre@tenderpulse.eu

# Frontend Check
URL: https://tenderpulse.eu
Method: GET
Interval: 5 minutes
Keyword: "TenderPulse"
Alert Contacts: alexandre@tenderpulse.eu

# Database Check (via API)
URL: https://api.tenderpulse.eu/api/v1/tenders?limit=1
Method: GET
Interval: 10 minutes
```

### Sentry Setup (Optional)
```bash
# Install Sentry CLI
npm install -g @sentry/cli

# Create projects
sentry-cli projects create tenderpulse-api
sentry-cli projects create tenderpulse-frontend

# Set environment variables
SENTRY_DSN=https://...@sentry.io/...
SENTRY_ENVIRONMENT=production
NEXT_PUBLIC_SENTRY_DSN=https://...@sentry.io/...
```

---

## 🔄 8. Automated Backups

### Daily Database Backup (Cron)
```bash
# On Railway/Render, add scheduled job
# Or use external service like GitHub Actions

name: Daily Backup
on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM daily
jobs:
  backup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Backup Database
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: |
          pg_dump $DATABASE_URL | gzip > backup-$(date +%Y%m%d).sql.gz
          # Upload to S3 or similar
```

---

## ✅ 9. Final Verification Checklist

### Pre-Launch Checklist
- [ ] Domain DNS records configured
- [ ] SSL certificates active
- [ ] Database deployed and migrated
- [ ] API deployed and healthy
- [ ] Frontend deployed and accessible
- [ ] Stripe webhooks working
- [ ] Email delivery working
- [ ] Authentication working
- [ ] Monitoring alerts configured
- [ ] Backups scheduled
- [ ] Error tracking active

### Test User Journey
```bash
# 1. User visits https://tenderpulse.eu
curl -I https://tenderpulse.eu

# 2. User signs up via Clerk
# Test in browser

# 3. User subscribes via Stripe
# Test checkout flow

# 4. User creates filter
# Test in app

# 5. User receives email alert
# Check Resend logs

# 6. API serves tender data
curl https://api.tenderpulse.eu/api/v1/tenders?limit=5
```

### Performance Verification
```bash
# API response times
curl -w "@curl-format.txt" -s -o /dev/null https://api.tenderpulse.eu/api/v1/health

# Frontend loading time
curl -w "@curl-format.txt" -s -o /dev/null https://tenderpulse.eu

# Database query performance
psql $DATABASE_URL -c "EXPLAIN ANALYZE SELECT * FROM tenders LIMIT 10;"
```

---

## 🚨 Emergency Rollback

### API Rollback
```bash
# Railway
railway rollback

# Render
# Use dashboard to rollback to previous deployment
```

### Frontend Rollback
```bash
vercel rollback --prod
```

### Database Rollback
```bash
# Restore from backup
pg_restore --clean --no-owner --no-privileges -d $DATABASE_URL latest-backup.custom.gz
```

---

## 📞 Support & Maintenance

### Daily Operations
- Monitor uptime alerts
- Check ingestion status
- Review email delivery rates
- Monitor error rates

### Weekly Operations
- Review performance metrics
- Check security updates
- Analyze user growth
- Update documentation

### Monthly Operations
- Security audit
- Dependency updates
- Backup restoration test
- Performance optimization

---

*Production deployment guide for TenderPulse*
*Last updated: 2025-09-18*
