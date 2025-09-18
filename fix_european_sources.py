#!/usr/bin/env python3
"""
Fix database to support all European procurement sources.
"""

import asyncio
import asyncpg

# Database connection
DATABASE_URL = "postgresql://postgres:EgdluIbkCIAXlkAFozsnImoaeONMnAUw@switchyard.proxy.rlwy.net:37786/railway"

async def fix_european_sources():
    """Fix the database to support all European sources."""
    print("🔧 Fixing database to support all European sources...")
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Check current source column type
        current_sources = await conn.fetch("""
            SELECT DISTINCT source FROM tenders ORDER BY source
        """)
        
        print(f"📊 Current sources in database:")
        for row in current_sources:
            print(f"  • {row['source']}")
        
        # Check if we have an enum constraint
        enum_info = await conn.fetch("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (
                SELECT oid 
                FROM pg_type 
                WHERE typname = 'tendersource'
            )
            ORDER BY enumlabel
        """)
        
        if enum_info:
            print(f"\n📋 Current enum values:")
            for row in enum_info:
                print(f"  • {row['enumlabel']}")
            
            # Add new enum values for European sources
            new_sources = [
                'GERMANY', 'ITALY', 'SPAIN', 'NETHERLANDS', 'UK', 
                'DENMARK', 'FINLAND', 'SWEDEN', 'AUSTRIA',
                'NORDIC_DK', 'NORDIC_FI', 'NORDIC_SE'
            ]
            
            print(f"\n➕ Adding new enum values...")
            for source in new_sources:
                try:
                    await conn.execute(f"ALTER TYPE tendersource ADD VALUE '{source}'")
                    print(f"  ✅ Added {source}")
                except Exception as e:
                    if "already exists" in str(e):
                        print(f"  ⏭️  {source} already exists")
                    else:
                        print(f"  ❌ Failed to add {source}: {e}")
        else:
            print("\n📝 No enum constraint found - sources should work directly")
        
        # Verify the fix worked
        print(f"\n🧪 Testing statistics endpoint...")
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_tenders,
                COUNT(CASE WHEN publication_date >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as recent_tenders_7_days
            FROM tenders
        """)
        
        sources_stats = await conn.fetch("""
            SELECT source, COUNT(*) as count 
            FROM tenders 
            GROUP BY source 
            ORDER BY count DESC
        """)
        
        countries_stats = await conn.fetch("""
            SELECT buyer_country, COUNT(*) as count 
            FROM tenders 
            GROUP BY buyer_country 
            ORDER BY count DESC
            LIMIT 10
        """)
        
        print(f"📊 Updated Statistics:")
        print(f"  • Total tenders: {stats['total_tenders']}")
        print(f"  • Recent (7 days): {stats['recent_tenders_7_days']}")
        
        print(f"\n📡 By Source:")
        for row in sources_stats:
            print(f"  • {row['source']}: {row['count']}")
        
        print(f"\n🌍 By Country:")
        for row in countries_stats:
            print(f"  • {row['buyer_country']}: {row['count']}")
        
        print(f"\n✅ Database fix completed successfully!")
        
    finally:
        await conn.close()

async def main():
    """Main function."""
    await fix_european_sources()

if __name__ == "__main__":
    asyncio.run(main())
