-- =============================================================================
-- TenderPulse Programmatic SEO Database Schema
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Tenders Table (Enhanced for SEO)
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS tenders (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    country VARCHAR(50) NOT NULL,
    category VARCHAR(100) NOT NULL,
    year INTEGER NOT NULL,
    budget_band VARCHAR(50) NOT NULL,
    deadline DATE NOT NULL,
    url TEXT NOT NULL,
    value_amount DECIMAL(15,2),
    currency VARCHAR(3) DEFAULT 'EUR',
    cpv_codes TEXT[],
    buyer_name VARCHAR(500),
    buyer_country VARCHAR(2),
    source VARCHAR(50),
    summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_tenders_country ON tenders(country);
CREATE INDEX IF NOT EXISTS idx_tenders_category ON tenders(category);
CREATE INDEX IF NOT EXISTS idx_tenders_year ON tenders(year);
CREATE INDEX IF NOT EXISTS idx_tenders_budget ON tenders(budget_band);
CREATE INDEX IF NOT EXISTS idx_tenders_deadline ON tenders(deadline);
CREATE INDEX IF NOT EXISTS idx_tenders_combo ON tenders(country, category, year, budget_band);
CREATE INDEX IF NOT EXISTS idx_tenders_value ON tenders(value_amount);
CREATE INDEX IF NOT EXISTS idx_tenders_cpv ON tenders USING GIN(cpv_codes);

-- -----------------------------------------------------------------------------
-- 2. Page Intros Table (GPT-generated content cache)
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS page_intros (
    id SERIAL PRIMARY KEY,
    country VARCHAR(50) NOT NULL,
    category VARCHAR(100) NOT NULL,
    year INTEGER NOT NULL,
    budget VARCHAR(50) NOT NULL,
    intro_text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(country, category, year, budget)
);

-- Create index for lookups
CREATE INDEX IF NOT EXISTS idx_page_intros_combo ON page_intros(country, category, year, budget);

-- -----------------------------------------------------------------------------
-- 3. SEO Pages Table (Track page performance)
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS seo_pages (
    id SERIAL PRIMARY KEY,
    page_type VARCHAR(50) NOT NULL, -- 'country', 'category', 'year', 'budget', 'combination'
    country VARCHAR(50),
    category VARCHAR(100),
    year INTEGER,
    budget VARCHAR(50),
    page_url VARCHAR(500) NOT NULL UNIQUE,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    keywords TEXT[],
    tender_count INTEGER DEFAULT 0,
    total_value DECIMAL(15,2) DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for SEO pages
CREATE INDEX IF NOT EXISTS idx_seo_pages_type ON seo_pages(page_type);
CREATE INDEX IF NOT EXISTS idx_seo_pages_url ON seo_pages(page_url);
CREATE INDEX IF NOT EXISTS idx_seo_pages_combo ON seo_pages(country, category, year, budget);

-- -----------------------------------------------------------------------------
-- 4. Sample Data (for testing)
-- -----------------------------------------------------------------------------

-- Sample countries (EU)
INSERT INTO tenders (title, country, category, year, budget_band, deadline, url, value_amount, currency, cpv_codes, buyer_name, buyer_country, source) VALUES
('IT Infrastructure Modernization', 'Germany', 'Information Technology', 2024, '€500K-€2M', '2024-12-15', 'https://ted.europa.eu/sample1', 1500000, 'EUR', ARRAY['72000000', '48000000'], 'Bundesministerium für Digitales', 'DE', 'TED'),
('Road Construction Project', 'France', 'Construction', 2024, '€2M-€10M', '2024-11-30', 'https://ted.europa.eu/sample2', 5000000, 'EUR', ARRAY['45000000', '60100000'], 'Ministère de la Transition écologique', 'FR', 'TED'),
('Healthcare Equipment Supply', 'Netherlands', 'Medical Equipment', 2024, '€100K-€500K', '2024-10-20', 'https://ted.europa.eu/sample3', 350000, 'EUR', ARRAY['33100000', '85000000'], 'Rijksinstituut voor Volksgezondheid', 'NL', 'TED'),
('Software Development Services', 'Germany', 'Information Technology', 2025, '€500K-€2M', '2025-01-15', 'https://ted.europa.eu/sample4', 800000, 'EUR', ARRAY['72000000', '79400000'], 'Bundesagentur für Arbeit', 'DE', 'TED'),
('Environmental Consulting', 'Spain', 'Consulting', 2024, '€100K-€500K', '2024-12-01', 'https://ted.europa.eu/sample5', 250000, 'EUR', ARRAY['79400000', '90000000'], 'Ministerio para la Transición Ecológica', 'ES', 'TED'),
('Public Transport Services', 'United Kingdom', 'Transportation', 2024, '€2M-€10M', '2024-11-15', 'https://ted.europa.eu/sample6', 7500000, 'EUR', ARRAY['60100000', '34600000'], 'Department for Transport', 'GB', 'TED'),
('Educational Technology', 'Italy', 'Information Technology', 2024, '€100K-€500K', '2024-10-30', 'https://ted.europa.eu/sample7', 400000, 'EUR', ARRAY['48000000', '80000000'], 'Ministero dell\'Istruzione', 'IT', 'TED'),
('Waste Management Services', 'Belgium', 'Environmental', 2024, '€500K-€2M', '2024-12-20', 'https://ted.europa.eu/sample8', 1200000, 'EUR', ARRAY['90000000', '75000000'], 'Service Public de Wallonie', 'BE', 'TED');

-- Sample page intro (will be generated by GPT in production)
INSERT INTO page_intros (country, category, year, budget, intro_text) VALUES
('Germany', 'Information Technology', 2024, '€500K-€2M', 
 'Explore current Information Technology tenders in Germany for 2024 within the €500K-€2M budget range. These opportunities are updated daily to ensure you have access to the latest government procurement contracts.');

-- -----------------------------------------------------------------------------
-- 5. Views for Analytics
-- -----------------------------------------------------------------------------

-- View for tender statistics by combination
CREATE OR REPLACE VIEW tender_stats AS
SELECT 
    country,
    category,
    year,
    budget_band,
    COUNT(*) as tender_count,
    SUM(value_amount) as total_value,
    AVG(value_amount) as avg_value,
    MIN(deadline) as earliest_deadline,
    MAX(deadline) as latest_deadline,
    COUNT(DISTINCT buyer_name) as unique_buyers
FROM tenders
GROUP BY country, category, year, budget_band;

-- View for country statistics
CREATE OR REPLACE VIEW country_stats AS
SELECT 
    country,
    COUNT(*) as total_tenders,
    COUNT(DISTINCT category) as categories,
    COUNT(DISTINCT year) as years,
    SUM(value_amount) as total_value,
    AVG(value_amount) as avg_value
FROM tenders
GROUP BY country
ORDER BY total_tenders DESC;

-- View for category statistics
CREATE OR REPLACE VIEW category_stats AS
SELECT 
    category,
    COUNT(*) as total_tenders,
    COUNT(DISTINCT country) as countries,
    COUNT(DISTINCT year) as years,
    SUM(value_amount) as total_value,
    AVG(value_amount) as avg_value
FROM tenders
GROUP BY category
ORDER BY total_tenders DESC;

-- -----------------------------------------------------------------------------
-- 6. Functions for SEO Page Generation
-- -----------------------------------------------------------------------------

-- Function to get or create page intro
CREATE OR REPLACE FUNCTION get_or_create_page_intro(
    p_country VARCHAR(50),
    p_category VARCHAR(100),
    p_year INTEGER,
    p_budget VARCHAR(50)
) RETURNS TEXT AS $$
DECLARE
    intro_text TEXT;
BEGIN
    -- Try to get existing intro
    SELECT page_intros.intro_text INTO intro_text
    FROM page_intros
    WHERE country = p_country 
      AND category = p_category 
      AND year = p_year 
      AND budget = p_budget;
    
    -- If not found, return a default intro
    IF intro_text IS NULL THEN
        intro_text := 'Discover ' || p_category || ' tenders in ' || p_country || 
                     ' for ' || p_year || ' within the ' || p_budget || 
                     ' budget range. Find the latest government procurement opportunities updated daily.';
    END IF;
    
    RETURN intro_text;
END;
$$ LANGUAGE plpgsql;

-- Function to get tender combinations for sitemap
CREATE OR REPLACE FUNCTION get_sitemap_combinations()
RETURNS TABLE(
    country VARCHAR(50),
    category VARCHAR(100),
    year INTEGER,
    budget VARCHAR(50),
    tender_count BIGINT,
    total_value DECIMAL(15,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.country,
        t.category,
        t.year,
        t.budget_band,
        COUNT(*) as tender_count,
        SUM(t.value_amount) as total_value
    FROM tenders t
    GROUP BY t.country, t.category, t.year, t.budget_band
    HAVING COUNT(*) >= 1  -- Only include combinations with at least 1 tender
    ORDER BY COUNT(*) DESC;
END;
$$ LANGUAGE plpgsql;

-- -----------------------------------------------------------------------------
-- 7. Row Level Security (if needed)
-- -----------------------------------------------------------------------------

-- Enable RLS on tenders table (optional)
-- ALTER TABLE tenders ENABLE ROW LEVEL SECURITY;

-- Create policy for public read access
-- CREATE POLICY "Public read access" ON tenders FOR SELECT USING (true);

-- -----------------------------------------------------------------------------
-- 8. Triggers for automatic updates
-- -----------------------------------------------------------------------------

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers
CREATE TRIGGER update_tenders_updated_at 
    BEFORE UPDATE ON tenders 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_seo_pages_updated_at 
    BEFORE UPDATE ON seo_pages 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
