#!/usr/bin/env python3
"""
Simple script to run the user profiles migration directly.
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append('app')

async def run_migration():
    """Run the user profiles migration."""
    try:
        from app.db.session import engine
        from app.db.models import Base, UserProfile
        from sqlalchemy import text
        
        print("🔄 Running user profiles migration...")
        
        async with engine.begin() as conn:
            # Check if user_profiles table already exists
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'user_profiles'
                );
            """))
            
            table_exists = result.scalar()
            
            if table_exists:
                print("✅ user_profiles table already exists")
                return True
            
            # Create the user_profiles table
            print("📝 Creating user_profiles table...")
            
            await conn.execute(text("""
                CREATE TABLE user_profiles (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL UNIQUE,
                    company_name VARCHAR(255),
                    target_value_range INTEGER[],
                    preferred_countries VARCHAR(2)[],
                    cpv_expertise VARCHAR(10)[],
                    company_size VARCHAR(50),
                    experience_level VARCHAR(50),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
            """))
            
            # Create indexes
            await conn.execute(text("""
                CREATE INDEX ix_user_profiles_id ON user_profiles (id);
            """))
            
            await conn.execute(text("""
                CREATE INDEX ix_user_profiles_user_id ON user_profiles (user_id);
            """))
            
            print("✅ user_profiles table created successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_migration())
    if success:
        print("🎉 Migration completed successfully!")
    else:
        print("💥 Migration failed!")
        sys.exit(1)
