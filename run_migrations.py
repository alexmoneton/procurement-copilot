#!/usr/bin/env python3
"""
Script to run Alembic migrations remotely via Railway deployment.
"""

import asyncio
import asyncpg
import os

# Database connection details from Railway
DATABASE_URL = "postgresql://postgres:EgdluIbkCIAXlkAFozsnImoaeONMnAUw@switchyard.proxy.rlwy.net:37786/railway"

async def check_tables():
    """Check what tables exist in the database."""
    print("🔍 Checking existing tables...")
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Get list of tables
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        print(f"Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table['table_name']}")
            
        # Check if main tables exist
        table_names = [t['table_name'] for t in tables]
        required_tables = ['users', 'tenders', 'saved_filters', 'alerts', 'companies', 'awards']
        
        missing_tables = [t for t in required_tables if t not in table_names]
        if missing_tables:
            print(f"\n❌ Missing required tables: {missing_tables}")
        else:
            print(f"\n✅ All required tables exist!")
            
    finally:
        await conn.close()

async def create_tables_manually():
    """Create tables manually using SQL."""
    print("\n🔨 Creating tables manually...")
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Create users table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                full_name VARCHAR(255),
                is_active BOOLEAN DEFAULT true,
                stripe_customer_id VARCHAR(255),
                subscription_status VARCHAR(50) DEFAULT 'free',
                subscription_tier VARCHAR(50) DEFAULT 'free',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        print("✅ Users table created")
        
        # Create tenders table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tenders (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tender_ref VARCHAR(255) UNIQUE NOT NULL,
                source VARCHAR(50) NOT NULL,
                title TEXT NOT NULL,
                summary TEXT,
                publication_date DATE NOT NULL,
                deadline_date DATE,
                cpv_codes TEXT[] DEFAULT '{}',
                buyer_name TEXT,
                buyer_country VARCHAR(2) NOT NULL,
                value_amount DECIMAL,
                currency VARCHAR(3),
                url TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        print("✅ Tenders table created")
        
        # Create indexes for tenders
        await conn.execute("CREATE INDEX IF NOT EXISTS ix_tenders_tender_ref ON tenders (tender_ref);")
        await conn.execute("CREATE INDEX IF NOT EXISTS ix_tenders_source ON tenders (source);")
        await conn.execute("CREATE INDEX IF NOT EXISTS ix_tenders_publication_date ON tenders (publication_date);")
        await conn.execute("CREATE INDEX IF NOT EXISTS ix_tenders_buyer_country ON tenders (buyer_country);")
        await conn.execute("CREATE INDEX IF NOT EXISTS ix_tenders_cpv_codes ON tenders USING GIN (cpv_codes);")
        print("✅ Tenders indexes created")
        
        # Create saved_filters table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS saved_filters (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                keywords TEXT[] DEFAULT '{}',
                cpv_codes TEXT[] DEFAULT '{}',
                countries TEXT[] DEFAULT '{}',
                min_value DECIMAL,
                max_value DECIMAL,
                notify_frequency VARCHAR(20) DEFAULT 'daily',
                last_notified_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        print("✅ Saved filters table created")
        
        # Create alerts table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                filter_id UUID NOT NULL REFERENCES saved_filters(id) ON DELETE CASCADE,
                tender_id UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
                alert_type VARCHAR(50) NOT NULL DEFAULT 'new_tender',
                sent_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        print("✅ Alerts table created")
        
        # Create companies table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name TEXT NOT NULL,
                country VARCHAR(2),
                domain VARCHAR(255),
                email VARCHAR(255),
                phone VARCHAR(50),
                address TEXT,
                industry VARCHAR(100),
                size_category VARCHAR(50),
                confidence_score FLOAT DEFAULT 0.0,
                last_contacted TIMESTAMP WITH TIME ZONE,
                contact_status VARCHAR(50) DEFAULT 'not_contacted',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        print("✅ Companies table created")
        
        # Create awards table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS awards (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tender_ref VARCHAR(255) NOT NULL,
                winner_name TEXT NOT NULL,
                winner_country VARCHAR(2),
                award_value DECIMAL,
                award_currency VARCHAR(3),
                award_date DATE,
                source VARCHAR(50) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        print("✅ Awards table created")
        
        print("\n🎉 All tables created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
    finally:
        await conn.close()

async def main():
    """Main function."""
    print("🚀 Running Database Migration Script")
    print("=" * 40)
    
    await check_tables()
    await create_tables_manually()
    
    print("\n🔍 Checking tables after creation...")
    await check_tables()

if __name__ == "__main__":
    asyncio.run(main())
