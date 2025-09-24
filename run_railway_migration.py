#!/usr/bin/env python3
"""Script to run database migrations on Railway."""

import os
import sys
import asyncio
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from alembic.config import Config
from alembic import command

def run_migrations():
    """Run database migrations."""
    print("🔄 Running database migrations...")
    
    # Set up Alembic configuration
    alembic_cfg = Config(str(backend_dir / "app" / "alembic.ini"))
    
    try:
        # Run migrations
        command.upgrade(alembic_cfg, "head")
        print("✅ Database migrations completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
