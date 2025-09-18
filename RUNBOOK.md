# TenderPulse Operations Runbook

## 🚨 Emergency Response

### Quick Reference
- **RTO Target**: < 2 hours
- **RPO Target**: < 24 hours (daily backups)
- **On-call**: Single operator (Alexandre)
- **Escalation**: Email → Slack → Phone

---

## 📊 Monitoring & Alerts

### Health Endpoints
- **API Health**: `https://api.tenderpulse.eu/api/v1/health`
- **Frontend Health**: `https://tenderpulse.eu/health`
- **Metrics**: `https://api.tenderpulse.eu/api/v1/metrics`

### Key Metrics
- **Response Time**: < 500ms P95
- **Uptime**: > 99.5%
- **Data Freshness**: Tenders ingested < 6 hours ago
- **Email Delivery**: > 95% success rate

### External Monitoring
```bash
# UptimeRobot Configuration
- API Health Check: https://api.tenderpulse.eu/api/v1/health (60s interval)
- Frontend Check: https://tenderpulse.eu (60s interval)
- Keyword Monitor: "TenderPulse" on frontend

# Better Stack / Pingdom
- Multi-region checks (Frankfurt, Paris, Amsterdam)
- SSL certificate monitoring
- DNS monitoring for tenderpulse.eu
```

---

## 🔧 Common Incidents

### 1. Data Ingestion Stops

**Symptoms:**
- No new tenders in last 6+ hours
- `/api/v1/health` shows old `last_ingest_time`
- Users complaining about stale data

**Diagnosis:**
```bash
# Check scheduler status
curl -s https://api.tenderpulse.eu/api/v1/health | jq '.last_ingest_time'

# Check logs for ingestion errors
# On Railway/Render dashboard, look for:
# - "Error with connector TED"
# - "Failed to fetch tenders"
# - Database connection errors
```

**Resolution:**
```bash
# Option 1: Trigger manual ingestion via API
curl -X POST https://api.tenderpulse.eu/api/v1/admin/trigger-ingest \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Option 2: SSH into container and run manually
python -m backend.app.tasks.jobs run_ingest

# Option 3: Restart the scheduler service
# Via Railway/Render dashboard: restart the service
```

**Prevention:**
- Monitor ingestion frequency
- Set up dead man's switch alert (no ingestion in 8h)
- Review TED API changes monthly

### 2. Email Alerts Failing

**Symptoms:**
- Users report missing daily alerts
- High bounce rate in Resend dashboard
- `/api/v1/health` shows email errors

**Diagnosis:**
```bash
# Check recent email logs
curl -s https://api.tenderpulse.eu/api/v1/admin/email-logs | jq '.recent_failures'

# Check Resend dashboard
# - Delivery rates
# - Bounce/complaint rates
# - Domain reputation

# Check DNS records
dig TXT mail.tenderpulse.eu  # SPF
dig TXT _domainkey.mail.tenderpulse.eu  # DKIM
```

**Resolution:**
```bash
# Option 1: Retry failed alerts
python -m backend.app.tasks.jobs send_alerts --retry-failed

# Option 2: Send test alert to verify system
python -m backend.app.tasks.jobs send_alerts --filter-id <filter_id> --test

# Option 3: Check and fix DNS records
# Verify SPF: v=spf1 include:_spf.resend.com ~all
# Verify DKIM from Resend dashboard
```

**Prevention:**
- Monitor email delivery rates
- Keep domain reputation high
- Warm up new domains gradually

### 3. Stripe Webhook Failures

**Symptoms:**
- Users charged but plan not updated
- Subscription status out of sync
- Webhook errors in Stripe dashboard

**Diagnosis:**
```bash
# Check webhook endpoint health
curl -s https://api.tenderpulse.eu/api/v1/billing/webhook-test

# Check Stripe dashboard for:
# - Failed webhook attempts
# - Response codes from our endpoint
# - Event retry status
```

**Resolution:**
```bash
# Option 1: Replay failed events from Stripe dashboard
# Go to Webhooks → Select endpoint → Recent deliveries → Retry

# Option 2: Manually sync user subscriptions
python -m backend.app.cli.users sync-subscriptions --user-id <user_id>

# Option 3: Rotate webhook secret if compromised
# Update STRIPE_WEBHOOK_SECRET in environment
# Update webhook URL in Stripe dashboard
```

**Prevention:**
- Monitor webhook success rate
- Set up idempotency for webhook processing
- Regular webhook endpoint testing

### 4. Database Issues

**Symptoms:**
- API returning 500 errors
- Connection timeouts
- Slow query performance

**Diagnosis:**
```bash
# Check database connectivity
pg_isready -h <db_host> -p <db_port>

# Check active connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# Check slow queries
psql $DATABASE_URL -c "SELECT query, mean_exec_time, calls FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"
```

**Resolution:**
```bash
# Option 1: Restart API to reset connections
# Via Railway/Render dashboard

# Option 2: Optimize slow queries
# Add indexes for common query patterns
psql $DATABASE_URL -c "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tenders_publication_date ON tenders(publication_date);"

# Option 3: Scale database resources
# Upgrade plan in Railway/Render dashboard
```

**Prevention:**
- Monitor connection pool usage
- Regular database maintenance
- Query performance monitoring

---

## 🔄 Routine Operations

### Daily Checks (Automated)
- [ ] Ingestion running (last 6 hours)
- [ ] Email alerts sent (daily at 07:30 CET)
- [ ] API response time < 500ms
- [ ] Database backup completed

### Weekly Checks (Manual)
- [ ] Review error logs and patterns
- [ ] Check email delivery rates
- [ ] Monitor user growth and usage
- [ ] Review Stripe transaction health

### Monthly Checks (Manual)
- [ ] Update dependencies (security patches)
- [ ] Review TED API for changes
- [ ] Analyze performance trends
- [ ] Backup restoration test

---

## 📋 Deployment Procedures

### Production Deployment
```bash
# 1. Pre-deployment checks
git status  # Ensure clean working directory
npm test    # Run all tests
docker build -t tenderpulse/api:latest .

# 2. Deploy API (Railway/Render)
git push origin main  # Triggers auto-deploy

# 3. Deploy Frontend (Vercel)
cd frontend
vercel --prod

# 4. Post-deployment verification
curl -s https://api.tenderpulse.eu/api/v1/health
curl -s https://tenderpulse.eu/health

# 5. Database migrations (if needed)
# Via Railway/Render console:
python -m alembic upgrade head
```

### Rollback Procedure
```bash
# 1. Identify last working commit
git log --oneline -10

# 2. Rollback API
git revert <bad_commit_hash>
git push origin main

# 3. Rollback Frontend
vercel rollback --prod

# 4. Database rollback (if migrations were run)
python -m alembic downgrade -1
```

---

## 🗄️ Backup & Recovery

### Database Backups
```bash
# Manual backup
./scripts/backup.sh production-$(date +%Y%m%d)

# Automated daily backup (cron)
0 2 * * * /app/scripts/backup.sh >> /var/log/backup.log 2>&1
```

### Recovery Procedures
```bash
# Full database restore
pg_restore --clean --no-owner --no-privileges -d $DATABASE_URL backup.custom.gz

# Point-in-time recovery (if supported by hosting provider)
# Contact Railway/Render support for PITR
```

### Backup Verification
```bash
# Test backup integrity monthly
pg_restore --list backup.custom.gz | head -20
```

---

## 📞 Escalation & Contacts

### Internal Team
- **Primary**: Alexandre (alexandre@tenderpulse.eu)
- **Backup**: TBD

### External Vendors
- **Railway Support**: help@railway.app
- **Render Support**: help@render.com
- **Vercel Support**: support@vercel.com
- **Resend Support**: support@resend.com
- **Stripe Support**: support@stripe.com

### Emergency Procedures
1. **Severity 1** (Site down): Immediate response required
   - Check status pages of all providers
   - Implement emergency maintenance page
   - Communicate via Twitter/email

2. **Severity 2** (Degraded service): Response within 2 hours
   - Investigate root cause
   - Implement temporary workaround
   - Schedule permanent fix

3. **Severity 3** (Minor issues): Response within 24 hours
   - Log issue for next maintenance window
   - Monitor for escalation

---

## 📚 Useful Commands

### Development
```bash
# Local development with production data
make dev-with-prod-data

# Run specific scraper
python -m backend.app.scrapers.ted fetch_tenders --limit 10

# Test email alerts
python -m backend.app.tasks.jobs send_alerts --dry-run
```

### Debugging
```bash
# Check API logs
curl -s https://api.tenderpulse.eu/api/v1/admin/logs | tail -100

# Database queries
psql $DATABASE_URL -c "SELECT COUNT(*) FROM tenders WHERE created_at > NOW() - INTERVAL '24 hours';"

# Performance profiling
curl -s https://api.tenderpulse.eu/api/v1/metrics | grep response_time
```

### Maintenance
```bash
# Clear old data (keep last 30 days)
python -m backend.app.cli.maintenance cleanup --days 30

# Rebuild search indexes
python -m backend.app.cli.maintenance reindex

# Update user statistics
python -m backend.app.cli.users update-stats
```

---

## 📈 Performance Baselines

### API Performance
- **Health endpoint**: < 50ms
- **Tenders list**: < 200ms
- **Tender detail**: < 100ms
- **Search**: < 300ms

### Database Performance
- **Connection time**: < 10ms
- **Query execution**: < 100ms average
- **Backup time**: < 30 minutes

### Email Performance
- **Alert generation**: < 5 minutes
- **Email delivery**: < 30 seconds
- **Bounce rate**: < 2%

---

*Last updated: 2025-09-18*
*Next review: 2025-10-18*
