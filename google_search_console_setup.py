#!/usr/bin/env python3
"""
Google Search Console Setup and Monitoring
Automated sitemap submission and performance tracking
"""

import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

class GoogleSearchConsoleManager:
    """Google Search Console management and monitoring"""
    
    def __init__(self, site_url: str = "https://tenderpulse.eu"):
        self.site_url = site_url
        self.sitemap_url = f"{site_url}/sitemap.xml"
        
    def generate_setup_instructions(self) -> str:
        """Generate step-by-step setup instructions"""
        return f"""
# Google Search Console Setup Instructions

## 🚀 Step 1: Add Property to Google Search Console

1. **Go to Google Search Console**: https://search.google.com/search-console/
2. **Click "Add Property"**
3. **Select "URL prefix"**
4. **Enter your domain**: {self.site_url}
5. **Click "Continue"**

## 🔐 Step 2: Verify Ownership

Choose one of these verification methods:

### Method A: HTML File Upload (Recommended)
1. **Download the verification file** from Google Search Console
2. **Upload it to your website root** (e.g., {self.site_url}/google[random-string].html)
3. **Click "Verify"**

### Method B: HTML Meta Tag
1. **Copy the meta tag** from Google Search Console
2. **Add it to your website's <head> section**
3. **Click "Verify"**

### Method C: Google Analytics (if you have it)
1. **Make sure Google Analytics is installed** on your site
2. **Select "Google Analytics"** as verification method
3. **Click "Verify"**

## 🗺️ Step 3: Submit Sitemap

1. **Go to "Sitemaps"** in the left sidebar
2. **Click "Add a new sitemap"**
3. **Enter sitemap URL**: {self.sitemap_url}
4. **Click "Submit"**

## 📊 Step 4: Monitor Performance

### Key Metrics to Track:
- **Total Clicks**: Organic traffic from Google
- **Total Impressions**: How often your pages appear in search
- **Average CTR**: Click-through rate (clicks/impressions)
- **Average Position**: Average ranking position

### Important Reports:
- **Performance**: Overall search performance
- **Coverage**: Which pages are indexed
- **Sitemaps**: Sitemap submission status
- **URL Inspection**: Check individual page indexing

## 🎯 Step 5: Optimize Based on Data

### Weekly Tasks:
1. **Check Coverage Report** for indexing issues
2. **Review Performance Report** for top-performing pages
3. **Monitor Sitemap Status** for submission errors
4. **Check URL Inspection** for specific page issues

### Monthly Tasks:
1. **Analyze Top Queries** and optimize for them
2. **Review Page Experience** metrics
3. **Check Mobile Usability** issues
4. **Monitor Core Web Vitals**

## 🔧 Step 6: Automated Monitoring Setup

Run the SEO monitoring script weekly:
```bash
python seo_monitoring_dashboard.py
```

## 📈 Expected Results Timeline:

- **Week 1-2**: Initial indexing of main pages
- **Week 3-4**: Programmatic pages start appearing
- **Month 2-3**: Significant organic traffic growth
- **Month 3-6**: Long-tail keyword rankings improve

## 🚨 Common Issues & Solutions:

### Sitemap Not Found (404)
- **Cause**: Sitemap route not deployed yet
- **Solution**: Wait for deployment or check sitemap URL

### Pages Not Indexed
- **Cause**: New pages need time to be discovered
- **Solution**: Submit individual URLs via URL Inspection

### Low Click-Through Rate
- **Cause**: Poor meta descriptions or titles
- **Solution**: Optimize meta tags for better CTR

### Slow Page Speed
- **Cause**: Large images or unoptimized code
- **Solution**: Optimize images and code

## 📞 Next Steps:

1. **Complete the setup** following these instructions
2. **Run the SEO audit** once setup is complete
3. **Set up weekly monitoring** with the dashboard
4. **Optimize based on data** from Search Console

## 🎯 Success Metrics:

- **Target**: 80%+ pages indexed within 3 months
- **Target**: 25%+ month-over-month organic traffic growth
- **Target**: 2-5% CTR from search results
- **Target**: Average position < 10 for target keywords
"""

    def generate_sitemap_submission_script(self) -> str:
        """Generate script to submit sitemap programmatically"""
        return f"""
# Sitemap Submission Script
# Run this after setting up Google Search Console API

import requests
import json

def submit_sitemap():
    # You'll need to set up Google Search Console API credentials
    # and get an access token
    
    sitemap_url = "{self.sitemap_url}"
    
    # This is a placeholder - you'll need to implement OAuth2 flow
    # for Google Search Console API
    
    print(f"Submitting sitemap: {{sitemap_url}}")
    print("Note: This requires Google Search Console API setup")
    print("For now, submit manually via the web interface")

if __name__ == "__main__":
    submit_sitemap()
"""

    def generate_monitoring_queries(self) -> str:
        """Generate SQL queries for monitoring SEO performance"""
        return f"""
-- SEO Performance Monitoring Queries
-- Run these in your database to track SEO metrics

-- 1. Track page views by SEO page type
SELECT 
    CASE 
        WHEN url LIKE '/seo/countries/%' THEN 'Country Pages'
        WHEN url LIKE '/seo/cpv-codes/%' THEN 'CPV Code Pages'
        WHEN url LIKE '/seo/value-ranges/%' THEN 'Value Range Pages'
        WHEN url LIKE '/seo/tenders/%' THEN 'Tender Combination Pages'
        ELSE 'Other Pages'
    END as page_type,
    COUNT(*) as page_views,
    COUNT(DISTINCT user_id) as unique_visitors
FROM page_views 
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY page_type
ORDER BY page_views DESC;

-- 2. Track conversion rates by page type
SELECT 
    CASE 
        WHEN url LIKE '/seo/countries/%' THEN 'Country Pages'
        WHEN url LIKE '/seo/cpv-codes/%' THEN 'CPV Code Pages'
        WHEN url LIKE '/seo/value-ranges/%' THEN 'Value Range Pages'
        WHEN url LIKE '/seo/tenders/%' THEN 'Tender Combination Pages'
        ELSE 'Other Pages'
    END as page_type,
    COUNT(*) as total_visits,
    COUNT(CASE WHEN converted = true THEN 1 END) as conversions,
    ROUND(COUNT(CASE WHEN converted = true THEN 1 END) * 100.0 / COUNT(*), 2) as conversion_rate
FROM user_sessions 
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY page_type
ORDER BY conversion_rate DESC;

-- 3. Track top-performing countries
SELECT 
    SUBSTRING(url FROM '/seo/countries/([^/]+)') as country,
    COUNT(*) as page_views,
    COUNT(DISTINCT user_id) as unique_visitors,
    AVG(session_duration) as avg_session_duration
FROM page_views 
WHERE url LIKE '/seo/countries/%'
    AND created_at >= NOW() - INTERVAL '30 days'
GROUP BY country
ORDER BY page_views DESC
LIMIT 10;

-- 4. Track top-performing CPV codes
SELECT 
    SUBSTRING(url FROM '/seo/cpv-codes/([^/]+)') as cpv_code,
    COUNT(*) as page_views,
    COUNT(DISTINCT user_id) as unique_visitors,
    AVG(session_duration) as avg_session_duration
FROM page_views 
WHERE url LIKE '/seo/cpv-codes/%'
    AND created_at >= NOW() - INTERVAL '30 days'
GROUP BY cpv_code
ORDER BY page_views DESC
LIMIT 10;

-- 5. Track organic traffic growth
SELECT 
    DATE_TRUNC('week', created_at) as week,
    COUNT(*) as total_sessions,
    COUNT(CASE WHEN traffic_source = 'organic' THEN 1 END) as organic_sessions,
    ROUND(COUNT(CASE WHEN traffic_source = 'organic' THEN 1 END) * 100.0 / COUNT(*), 2) as organic_percentage
FROM user_sessions 
WHERE created_at >= NOW() - INTERVAL '12 weeks'
GROUP BY week
ORDER BY week;
"""

def main():
    """Generate setup instructions and monitoring tools"""
    manager = GoogleSearchConsoleManager()
    
    # Generate setup instructions
    instructions = manager.generate_setup_instructions()
    
    # Save to file
    with open("google_search_console_setup.md", "w", encoding="utf-8") as f:
        f.write(instructions)
    
    # Generate sitemap submission script
    sitemap_script = manager.generate_sitemap_submission_script()
    with open("submit_sitemap.py", "w", encoding="utf-8") as f:
        f.write(sitemap_script)
    
    # Generate monitoring queries
    monitoring_queries = manager.generate_monitoring_queries()
    with open("seo_monitoring_queries.sql", "w", encoding="utf-8") as f:
        f.write(monitoring_queries)
    
    print("✅ Generated Google Search Console setup files:")
    print("📄 google_search_console_setup.md - Complete setup instructions")
    print("🐍 submit_sitemap.py - Sitemap submission script")
    print("🗄️ seo_monitoring_queries.sql - Database monitoring queries")
    print("\n🚀 Next steps:")
    print("1. Follow the instructions in google_search_console_setup.md")
    print("2. Run the SEO audit: python seo_monitoring_dashboard.py")
    print("3. Set up weekly monitoring with the generated queries")

if __name__ == "__main__":
    main()
