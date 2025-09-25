
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
