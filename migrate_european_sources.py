#!/usr/bin/env python3
"""
Database migration to support European procurement sources.
"""

import asyncio
import asyncpg

# Database connection
DATABASE_URL = "postgresql://postgres:EgdluIbkCIAXlkAFozsnImoaeONMnAUw@switchyard.proxy.rlwy.net:37786/railway"

async def migrate_european_sources():
    """Migrate database to support European sources."""
    print("🚀 Starting European sources migration...")
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Check if enum exists
        enum_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'tendersource'
            )
        """)
        
        if enum_exists:
            print("📋 TenderSource enum exists - adding new values...")
            
            # Get current enum values
            current_values = await conn.fetch("""
                SELECT enumlabel 
                FROM pg_enum 
                WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'tendersource')
                ORDER BY enumlabel
            """)
            
            current_labels = [row['enumlabel'] for row in current_values]
            print(f"Current enum values: {current_labels}")
            
            # New European sources to add
            new_sources = [
                'GERMANY', 'ITALY', 'SPAIN', 'NETHERLANDS', 'UK',
                'DENMARK', 'FINLAND', 'SWEDEN', 'AUSTRIA',
                'NORDIC_DK', 'NORDIC_FI', 'NORDIC_SE'
            ]
            
            # Add new enum values
            for source in new_sources:
                if source not in current_labels:
                    try:
                        await conn.execute(f"ALTER TYPE tendersource ADD VALUE '{source}'")
                        print(f"  ✅ Added {source}")
                    except Exception as e:
                        print(f"  ❌ Failed to add {source}: {e}")
                else:
                    print(f"  ⏭️  {source} already exists")
                    
        else:
            print("📝 TenderSource enum doesn't exist - creating it...")
            
            # Create the enum type with all values
            all_sources = [
                'TED', 'BOAMP_FR',
                'GERMANY', 'ITALY', 'SPAIN', 'NETHERLANDS', 'UK',
                'DENMARK', 'FINLAND', 'SWEDEN', 'AUSTRIA',
                'NORDIC_DK', 'NORDIC_FI', 'NORDIC_SE'
            ]
            
            enum_values = "', '".join(all_sources)
            await conn.execute(f"CREATE TYPE tendersource AS ENUM ('{enum_values}')")
            print("✅ Created TenderSource enum with all European sources")
            
            # Update the tenders table to use the enum (if not already)
            try:
                await conn.execute("""
                    ALTER TABLE tenders 
                    ALTER COLUMN source TYPE tendersource 
                    USING source::text::tendersource
                """)
                print("✅ Updated tenders.source column to use enum")
            except Exception as e:
                print(f"⚠️  Column might already be using enum: {e}")
        
        # Verify the migration worked
        print("\n🧪 Testing migration...")
        
        # Check final enum values
        final_values = await conn.fetch("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'tendersource')
            ORDER BY enumlabel
        """)
        
        final_labels = [row['enumlabel'] for row in final_values]
        print(f"✅ Final enum values: {final_labels}")
        
        # Test statistics query
        try:
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_tenders,
                    COUNT(CASE WHEN publication_date >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as recent_tenders_7_days
                FROM tenders
            """)
            
            source_stats = await conn.fetch("""
                SELECT source, COUNT(*) as count 
                FROM tenders 
                GROUP BY source 
                ORDER BY count DESC
            """)
            
            print(f"\n📊 Migration verification:")
            print(f"  • Total tenders: {stats['total_tenders']}")
            print(f"  • Recent (7 days): {stats['recent_tenders_7_days']}")
            print(f"  • Sources working: {len(source_stats)} different sources")
            
            print(f"✅ Migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Migration verification failed: {e}")
            raise
            
    finally:
        await conn.close()

async def main():
    """Main function."""
    await migrate_european_sources()

if __name__ == "__main__":
    asyncio.run(main())
