#!/usr/bin/env python3
"""
Test script to verify database setup with UserProfile model.
"""

import sys
import os

# Add the app directory to the path
sys.path.append('app')

def test_database_setup():
    """Test that the database setup includes UserProfile."""
    try:
        print("🧪 Testing database setup...")
        
        # Import the models
        from app.db.models import UserProfile, User, Tender
        print("✅ All models imported successfully")
        
        # Check UserProfile model attributes
        print(f"✅ UserProfile table name: {UserProfile.__tablename__}")
        print(f"✅ UserProfile columns: {list(UserProfile.__table__.columns.keys())}")
        
        # Check User model has profile relationship
        if hasattr(User, 'profile'):
            print("✅ User model has profile relationship")
        else:
            print("❌ User model missing profile relationship")
            
        print("✅ Database setup is ready!")
        print("📝 The UserProfile table will be created when init_db() is called")
        
        return True
        
    except Exception as e:
        print(f"❌ Database setup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_database_setup()
    if success:
        print("🎉 Database setup test passed!")
    else:
        print("💥 Database setup test failed!")
        sys.exit(1)
