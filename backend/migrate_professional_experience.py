"""
Database Migration Script for Professional Experience
Run this to add the professional_experience table to existing databases

Usage: python migrate_professional_experience.py
"""

from sqlalchemy import create_engine
from database import DATABASE_URL, SessionLocal
import models

def migrate_database():
    """Add professional_experience table to existing database"""

    print("🔄 Starting database migration...")

    try:
        # Create engine
        engine = create_engine(DATABASE_URL)

        # Create the new table
        print("📋 Creating professional_experience table...")
        models.ProfessionalExperience.__table__.create(engine, checkfirst=True)
        print("✅ Table created successfully")

        print("\n✅ Migration completed successfully!")
        print("\nNext steps:")
        print("1. Restart your backend server")
        print("2. Doctors can now add their professional experience in their dashboard")
        print("3. Students will see professional experience when viewing doctor profiles")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure the backend server is not running")
        print("2. Check that DATABASE_URL is correctly set in your .env file")
        print("3. Ensure you have write permissions to the database file")

if __name__ == "__main__":
    migrate_database()
