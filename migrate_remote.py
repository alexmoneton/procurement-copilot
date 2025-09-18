#!/usr/bin/env python3
"""
Run Alembic migrations on the remote Railway database.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Set environment variables for Railway database
os.environ.update({
    "DB_HOST": "postgres.railway.internal",
    "DB_PORT": "5432",
    "DB_NAME": "railway", 
    "DB_USER": "postgres",
    "DB_PASSWORD": "EgdlulbkCTAXlkAFozsnImoacOWMnAlw",
    "SECRET_KEY": "temp-secret-for-migration",
    "ENVIRONMENT": "production"
})

def main():
    try:
        # Import after setting environment variables
        from alembic.config import Config
        from alembic import command
        
        # Set up Alembic config
        alembic_cfg = Config("backend/app/alembic.ini")
        alembic_cfg.set_main_option("script_location", "backend/app/migrations")
        
        print("🚀 Running database migrations on Railway PostgreSQL...")
        print(f"Host: {os.environ['DB_HOST']}")
        print(f"Database: {os.environ['DB_NAME']}")
        
        # Run migrations
        command.upgrade(alembic_cfg, "head")
        
        print("✅ Migrations completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
