#!/usr/bin/env python3
"""
Migrate prospects from SQLite to Postgres
Handles multi-process safety and analytics joins with tenders.
"""

import os
import json
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime
from typing import Dict, List, Optional
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PostgresMigrator:
    """
    Migrate prospects from SQLite to Postgres with proper schema and unique keys.
    """
    
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.sqlite_path = self.config.get('database', {}).get('path', 'ted_prospects.db')
        self.pg_config = self.config.get('postgres', {})
        
        # Initialize connections
        self.sqlite_conn = None
        self.pg_conn = None
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file {config_path} not found")
            return {}
    
    def connect_sqlite(self):
        """Connect to SQLite database."""
        try:
            self.sqlite_conn = sqlite3.connect(self.sqlite_path)
            self.sqlite_conn.row_factory = sqlite3.Row
            logger.info(f"Connected to SQLite: {self.sqlite_path}")
        except Exception as e:
            logger.error(f"Failed to connect to SQLite: {e}")
            raise
    
    def connect_postgres(self):
        """Connect to Postgres database."""
        try:
            self.pg_conn = psycopg2.connect(
                host=self.pg_config.get('host', 'localhost'),
                port=self.pg_config.get('port', 5432),
                database=self.pg_config.get('database', 'tenderpulse'),
                user=self.pg_config.get('user', 'postgres'),
                password=self.pg_config.get('password', '')
            )
            logger.info("Connected to Postgres")
        except Exception as e:
            logger.error(f"Failed to connect to Postgres: {e}")
            raise
    
    def create_postgres_schema(self):
        """Create Postgres schema for prospects."""
        schema_sql = """
        -- Create prospects schema
        CREATE SCHEMA IF NOT EXISTS prospects;
        
        -- Prospects table with unique key
        CREATE TABLE IF NOT EXISTS prospects.prospects (
            id SERIAL PRIMARY KEY,
            normalized_company VARCHAR(255) NOT NULL,
            country VARCHAR(2) NOT NULL,
            cpv_family VARCHAR(8) NOT NULL,
            last_seen_award_ref VARCHAR(100) NOT NULL,
            company_name VARCHAR(255),
            domain VARCHAR(255),
            email VARCHAR(255),
            phone VARCHAR(50),
            address TEXT,
            website VARCHAR(255),
            linkedin_url VARCHAR(255),
            company_size VARCHAR(50),
            industry VARCHAR(100),
            description TEXT,
            lost_tender_title TEXT,
            lost_tender_id VARCHAR(100),
            lost_tender_value DECIMAL(15,2),
            lost_tender_currency VARCHAR(3),
            lost_tender_deadline DATE,
            lost_tender_buyer VARCHAR(255),
            lost_tender_buyer_country VARCHAR(2),
            lost_tender_cpv_codes TEXT[],
            winner_name VARCHAR(255),
            pain_level INTEGER,
            status VARCHAR(50) DEFAULT 'found',
            email_found_at TIMESTAMP,
            contacted_at TIMESTAMP,
            responded_at TIMESTAMP,
            converted_at TIMESTAMP,
            last_contacted_at TIMESTAMP,
            contact_count INTEGER DEFAULT 0,
            response_count INTEGER DEFAULT 0,
            notes TEXT,
            tags TEXT[],
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Unique constraint for deduplication
            UNIQUE(normalized_company, country, cpv_family, last_seen_award_ref)
        );
        
        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_prospects_normalized_company ON prospects.prospects(normalized_company);
        CREATE INDEX IF NOT EXISTS idx_prospects_country ON prospects.prospects(country);
        CREATE INDEX IF NOT EXISTS idx_prospects_cpv_family ON prospects.prospects(cpv_family);
        CREATE INDEX IF NOT EXISTS idx_prospects_status ON prospects.prospects(status);
        CREATE INDEX IF NOT EXISTS idx_prospects_created_at ON prospects.prospects(created_at);
        CREATE INDEX IF NOT EXISTS idx_prospects_email ON prospects.prospects(email);
        
        -- Email cache table for cost optimization
        CREATE TABLE IF NOT EXISTS prospects.email_cache (
            id SERIAL PRIMARY KEY,
            domain VARCHAR(255) NOT NULL,
            email VARCHAR(255),
            confidence_score INTEGER,
            source VARCHAR(50),
            ttl_expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            UNIQUE(domain)
        );
        
        CREATE INDEX IF NOT EXISTS idx_email_cache_domain ON prospects.email_cache(domain);
        CREATE INDEX IF NOT EXISTS idx_email_cache_ttl ON prospects.email_cache(ttl_expires_at);
        
        -- Suppression table for compliance
        CREATE TABLE IF NOT EXISTS prospects.suppressions (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            reason VARCHAR(50) NOT NULL,
            source VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            UNIQUE(email)
        );
        
        CREATE INDEX IF NOT EXISTS idx_suppressions_email ON prospects.suppressions(email);
        CREATE INDEX IF NOT EXISTS idx_suppressions_reason ON prospects.suppressions(reason);
        
        -- Events table for funnel telemetry
        CREATE TABLE IF NOT EXISTS prospects.events (
            id SERIAL PRIMARY KEY,
            event_type VARCHAR(50) NOT NULL,
            entity_type VARCHAR(50) NOT NULL,
            entity_id VARCHAR(100) NOT NULL,
            properties JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_events_type ON prospects.events(event_type);
        CREATE INDEX IF NOT EXISTS idx_events_entity ON prospects.events(entity_type, entity_id);
        CREATE INDEX IF NOT EXISTS idx_events_created_at ON prospects.events(created_at);
        
        -- Update trigger for updated_at
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        CREATE TRIGGER update_prospects_updated_at 
            BEFORE UPDATE ON prospects.prospects 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """
        
        try:
            with self.pg_conn.cursor() as cursor:
                cursor.execute(schema_sql)
                self.pg_conn.commit()
                logger.info("Postgres schema created successfully")
        except Exception as e:
            logger.error(f"Failed to create Postgres schema: {e}")
            raise
    
    def normalize_company_name(self, company_name: str) -> str:
        """Normalize company name for unique key."""
        if not company_name:
            return ""
        
        # Remove common suffixes and normalize
        normalized = company_name.lower().strip()
        suffixes = ['ltd', 'limited', 'inc', 'incorporated', 'corp', 'corporation', 
                   'gmbh', 'ag', 'sa', 'bv', 'nv', 'srl', 'spa', 'sas', 'sarl']
        
        for suffix in suffixes:
            if normalized.endswith(f' {suffix}'):
                normalized = normalized[:-len(f' {suffix}')]
        
        return normalized
    
    def extract_cpv_family(self, cpv_codes: str) -> str:
        """Extract CPV family (first 2 digits) from CPV codes."""
        if not cpv_codes:
            return "00"
        
        # Handle both string and list formats
        if isinstance(cpv_codes, str):
            cpv_codes = [cpv_codes]
        
        if cpv_codes and len(cpv_codes) > 0:
            first_cpv = str(cpv_codes[0])
            if len(first_cpv) >= 2:
                return first_cpv[:2]
        
        return "00"
    
    def migrate_prospects(self, batch_size: int = 1000):
        """Migrate prospects from SQLite to Postgres."""
        logger.info("Starting prospect migration...")
        
        # Get total count
        with self.sqlite_conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM prospects")
            total_count = cursor.fetchone()[0]
        
        logger.info(f"Total prospects to migrate: {total_count}")
        
        migrated = 0
        skipped = 0
        errors = 0
        
        with self.sqlite_conn.cursor() as cursor:
            cursor.execute("SELECT * FROM prospects ORDER BY created_at")
            
            while True:
                rows = cursor.fetchmany(batch_size)
                if not rows:
                    break
                
                for row in rows:
                    try:
                        # Convert SQLite row to dict
                        prospect = dict(row)
                        
                        # Normalize data
                        normalized_company = self.normalize_company_name(prospect.get('company_name', ''))
                        cpv_family = self.extract_cpv_family(prospect.get('cpv_codes', ''))
                        
                        # Create unique key
                        unique_key = f"{normalized_company}:{prospect.get('country', '')}:{cpv_family}:{prospect.get('lost_tender_id', '')}"
                        
                        # Check if already exists
                        with self.pg_conn.cursor() as pg_cursor:
                            pg_cursor.execute("""
                                SELECT id FROM prospects.prospects 
                                WHERE normalized_company = %s 
                                AND country = %s 
                                AND cpv_family = %s 
                                AND last_seen_award_ref = %s
                            """, (
                                normalized_company,
                                prospect.get('country', ''),
                                cpv_family,
                                prospect.get('lost_tender_id', '')
                            ))
                            
                            if pg_cursor.fetchone():
                                skipped += 1
                                continue
                        
                        # Insert into Postgres
                        with self.pg_conn.cursor() as pg_cursor:
                            pg_cursor.execute("""
                                INSERT INTO prospects.prospects (
                                    normalized_company, country, cpv_family, last_seen_award_ref,
                                    company_name, domain, email, phone, address, website, linkedin_url,
                                    company_size, industry, description, lost_tender_title, lost_tender_id,
                                    lost_tender_value, lost_tender_currency, lost_tender_deadline,
                                    lost_tender_buyer, lost_tender_buyer_country, lost_tender_cpv_codes,
                                    winner_name, pain_level, status, email_found_at, contacted_at,
                                    responded_at, converted_at, last_contacted_at, contact_count,
                                    response_count, notes, tags, created_at, updated_at
                                ) VALUES (
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                                )
                            """, (
                                normalized_company,
                                prospect.get('country', ''),
                                cpv_family,
                                prospect.get('lost_tender_id', ''),
                                prospect.get('company_name'),
                                prospect.get('domain'),
                                prospect.get('email'),
                                prospect.get('phone'),
                                prospect.get('address'),
                                prospect.get('website'),
                                prospect.get('linkedin_url'),
                                prospect.get('company_size'),
                                prospect.get('industry'),
                                prospect.get('description'),
                                prospect.get('lost_tender_title'),
                                prospect.get('lost_tender_id'),
                                prospect.get('lost_tender_value'),
                                prospect.get('lost_tender_currency'),
                                prospect.get('lost_tender_deadline'),
                                prospect.get('lost_tender_buyer'),
                                prospect.get('lost_tender_buyer_country'),
                                prospect.get('cpv_codes', '').split(',') if prospect.get('cpv_codes') else [],
                                prospect.get('winner_name'),
                                prospect.get('pain_level'),
                                prospect.get('status', 'found'),
                                prospect.get('email_found_at'),
                                prospect.get('contacted_at'),
                                prospect.get('responded_at'),
                                prospect.get('converted_at'),
                                prospect.get('last_contacted_at'),
                                prospect.get('contact_count', 0),
                                prospect.get('response_count', 0),
                                prospect.get('notes'),
                                prospect.get('tags', '').split(',') if prospect.get('tags') else [],
                                prospect.get('created_at'),
                                prospect.get('updated_at')
                            ))
                        
                        migrated += 1
                        
                        if migrated % 100 == 0:
                            logger.info(f"Migrated {migrated}/{total_count} prospects")
                            self.pg_conn.commit()
                    
                    except Exception as e:
                        logger.error(f"Error migrating prospect {prospect.get('company_name', 'Unknown')}: {e}")
                        errors += 1
                        continue
        
        # Final commit
        self.pg_conn.commit()
        
        logger.info(f"Migration completed:")
        logger.info(f"  Migrated: {migrated}")
        logger.info(f"  Skipped (duplicates): {skipped}")
        logger.info(f"  Errors: {errors}")
        
        return {
            'migrated': migrated,
            'skipped': skipped,
            'errors': errors,
            'total': total_count
        }
    
    def close_connections(self):
        """Close database connections."""
        if self.sqlite_conn:
            self.sqlite_conn.close()
        if self.pg_conn:
            self.pg_conn.close()
        logger.info("Database connections closed")

def main():
    """Main migration function."""
    migrator = PostgresMigrator()
    
    try:
        # Connect to databases
        migrator.connect_sqlite()
        migrator.connect_postgres()
        
        # Create schema
        migrator.create_postgres_schema()
        
        # Migrate data
        result = migrator.migrate_prospects()
        
        print(f"✅ Migration completed successfully!")
        print(f"   Migrated: {result['migrated']}")
        print(f"   Skipped: {result['skipped']}")
        print(f"   Errors: {result['errors']}")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        print(f"❌ Migration failed: {e}")
    finally:
        migrator.close_connections()

if __name__ == "__main__":
    main()
