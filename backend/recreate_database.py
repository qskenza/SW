"""
Database Recreation Script
Run this to recreate the database with the new Nurse table
"""

import os
from database import engine
from models import Base

def recreate_database():
    db_path = "healthcare.db"

    print("=" * 60)
    print("DATABASE RECREATION SCRIPT")
    print("=" * 60)

    # Check if database exists
    if os.path.exists(db_path):
        print(f"\n⚠️  Found existing database: {db_path}")
        response = input("❓ Do you want to DELETE it and create a new one? (yes/no): ")

        if response.lower() not in ['yes', 'y']:
            print("❌ Aborted. Database not modified.")
            return

        # Delete old database
        print(f"🗑️  Deleting old database...")
        os.remove(db_path)
        print(f"✅ Old database deleted")

    # Create new database with all tables
    print(f"\n🔨 Creating new database with all tables...")
    Base.metadata.create_all(bind=engine)
    print(f"✅ Database created successfully!")

    print("\n📊 Tables created:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")

    print("\n" + "=" * 60)
    print("✅ Database recreation complete!")
    print("=" * 60)
    print("\n💡 Next steps:")
    print("  1. Restart your backend server (python main.py)")
    print("  2. Register new users (student, doctor, nurse)")
    print("  3. Test all functionality")

if __name__ == "__main__":
    recreate_database()
