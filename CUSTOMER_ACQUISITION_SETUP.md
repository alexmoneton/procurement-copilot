# 🚀 TenderPulse Customer Acquisition Engine Setup

**Turn TED bid losers into paying customers automatically!**

## 🎯 What This Does

1. **Finds bid losers** from TED (companies that lost government contracts)
2. **Gets their email addresses** using Hunter.io
3. **Sends personalized outreach** mentioning their specific lost bid
4. **Tracks responses** and conversions
5. **Runs daily** to build your customer pipeline

## 💰 Expected Results

- **120+ prospects/month** (running daily)
- **15-25% email open rate** (highly targeted)
- **3-8% conversion rate** (pain-focused messaging)
- **€2,000-5,000/month revenue** within 90 days

## 🔧 Setup Instructions

### Step 1: Get API Keys

#### Hunter.io (Email Finding)
1. Go to [hunter.io](https://hunter.io)
2. Sign up for free account (50 searches/month)
3. Get API key from dashboard
4. **Upgrade to $49/month** for 1,000 searches (recommended)

#### Resend (Email Sending)
1. Go to [resend.com](https://resend.com)
2. Sign up for free account (100 emails/month)
3. Add your domain (tenderpulse.eu)
4. Get API key from dashboard
5. **Upgrade to $20/month** for 10,000 emails (recommended)

### Step 2: Configure Environment

```bash
# Copy the example environment file
cp env.customer_acquisition.example .env

# Edit with your API keys
nano .env
```

**Required variables:**
```bash
HUNTER_API_KEY=your_hunter_io_api_key_here
RESEND_API_KEY=your_resend_api_key_here
FROM_EMAIL=hello@tenderpulse.eu
FROM_NAME=Alex from TenderPulse
```

### Step 3: Install Dependencies

```bash
pip install httpx python-dotenv
```

### Step 4: Test the System

```bash
# Test email finding
python production_customer_acquisition.py test-email

# Run a single prospecting cycle
python production_customer_acquisition.py daily
```

### Step 5: Set Up Daily Automation

#### Option A: Cron Job (Linux/Mac)
```bash
# Edit crontab
crontab -e

# Add this line to run daily at 9 AM
0 9 * * * cd /path/to/procurement-copilot && python production_customer_acquisition.py daily
```

#### Option B: GitHub Actions (Cloud)
Create `.github/workflows/daily-prospecting.yml`:

```yaml
name: Daily Customer Acquisition
on:
  schedule:
    - cron: '0 9 * * *'  # 9 AM daily
jobs:
  prospect:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install httpx python-dotenv
      - run: python production_customer_acquisition.py daily
        env:
          HUNTER_API_KEY: ${{ secrets.HUNTER_API_KEY }}
          RESEND_API_KEY: ${{ secrets.RESEND_API_KEY }}
          FROM_EMAIL: ${{ secrets.FROM_EMAIL }}
          FROM_NAME: ${{ secrets.FROM_NAME }}
```

## 📊 Monitoring & Analytics

### View Current Prospects
```bash
python production_customer_acquisition.py prospects
```

### Database Schema
The system creates a SQLite database (`prospects.db`) with:

- **prospects** - Company details, contact info, status
- **outreach_emails** - Sent emails, opens, clicks, responses

### Key Metrics to Track
- **Daily prospects found**
- **Email finding success rate**
- **Email delivery rate**
- **Open rates by sector/country**
- **Response rates**
- **Conversion to trial/paid**

## 🎨 Email Personalization

The system generates emails like:

```
Subject: 5 new Construction opportunities in DE (like the €1.5M tender)

Hi [Name],

I noticed your company recently participated in this procurement:

📋 "Germany - Construction work - Cable installation project"
🏢 Buyer: Hamburg Public Works Authority  
💰 Value: €1,500,000
📅 Award Date: March 15, 2024

While that opportunity has closed, I found 3 similar contracts 
that might be perfect for your business:

1. Similar cable installation project in Berlin
   💰 Est. Value: €2,200,000
   🏢 Buyer: Berlin Infrastructure Department
   ⏰ Status: Open for bidding
   🔗 Link: [actual TED link]

[... more opportunities ...]

Here's the thing - most Construction companies miss 80% of 
relevant opportunities because they're scattered across 27+ 
different procurement portals.

That's exactly why we built TenderPulse.

[... rest of pitch ...]
```

## 🔥 Optimization Tips

### A/B Testing Subject Lines
Test these variations:
- "5 new [sector] opportunities in [country]"
- "Don't miss the next [buyer] contract"
- "Similar tenders to your recent [sector] bid"
- "Why you should have won that [value] contract"

### Best Send Times
- **Tuesday-Thursday, 9-11 AM** (highest open rates)
- **Avoid Mondays and Fridays**
- **Respect time zones** (EU business hours)

### Follow-Up Sequence
1. **Day 0**: Initial outreach
2. **Day 3**: "Did you see these opportunities?"
3. **Day 7**: "Last chance - 2 new tenders closing soon"
4. **Day 14**: "How's your procurement pipeline looking?"

### Sector-Specific Messaging
- **IT/Software**: Focus on "digital transformation" opportunities
- **Construction**: Emphasize "infrastructure investment" projects
- **Consulting**: Highlight "advisory services" contracts

## 📈 Scaling to €50K MRR

### Month 1: Foundation (€2K MRR)
- Run daily prospecting
- 120 prospects/month
- 15% conversion = 18 customers
- 18 × €99 = €1,782/month

### Month 3: Optimization (€8K MRR)
- A/B test email templates
- Add follow-up sequences
- Expand to all EU countries
- 500 prospects/month × 20% conversion = €9,900/month

### Month 6: Scale (€25K MRR)
- Add LinkedIn outreach
- Hire VA for email verification
- Add phone follow-up for high-value prospects
- 1,200 prospects/month × 25% conversion = €29,700/month

### Month 12: Automation (€50K MRR)
- Full automation with Zapier/Make
- Dedicated outreach team
- Enterprise sales for high-value prospects
- 2,000 prospects/month × 30% conversion = €59,400/month

## 🚨 Legal & Compliance

### GDPR Compliance
- ✅ **Legitimate interest** basis (B2B prospecting)
- ✅ **Opt-out link** in every email
- ✅ **Data retention** policy (delete after 2 years)
- ✅ **Consent tracking** for responses

### Email Best Practices
- ✅ **Authentic sender** (your real email)
- ✅ **Clear unsubscribe** option
- ✅ **Relevant content** (not spam)
- ✅ **Rate limiting** (max 50/day recommended)

## 🎊 Success Metrics

**Week 1 Goals:**
- [ ] 50+ prospects found
- [ ] 80%+ email finding success
- [ ] 20%+ email open rate
- [ ] 1+ response/trial signup

**Month 1 Goals:**
- [ ] 500+ prospects in database
- [ ] 100+ emails sent
- [ ] 15+ responses
- [ ] 5+ trial signups
- [ ] 2+ paid conversions

**Month 3 Goals:**
- [ ] 1,500+ prospects in database
- [ ] 25%+ email open rate
- [ ] 50+ trial signups
- [ ] €5,000+ MRR

## 🆘 Troubleshooting

### "No prospects found"
- Check TED API is working
- Expand date range or countries
- Lower minimum contract value

### "No emails found"
- Check Hunter.io API key
- Verify you have search credits
- Try alternative email finder (Apollo.io)

### "Emails not sending"
- Check Resend API key
- Verify domain authentication
- Check daily sending limits

### "Low open rates"
- A/B test subject lines
- Check sender reputation
- Verify email deliverability

## 🎯 Ready to Launch?

```bash
# Final test
python production_customer_acquisition.py daily

# If successful, set up daily automation
# Then watch your customer pipeline grow! 🚀
```

**This is your path to €50K MRR, habibi!** 💰
