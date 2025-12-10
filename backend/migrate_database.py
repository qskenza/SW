"""
Database Migration Script for Doctor Availability
Run this to add the doctor_availability table to existing databases

Usage: python migrate_availability.py
"""

from sqlalchemy import create_engine, text
from database import DATABASE_URL, SessionLocal
import models

def migrate_database():
    """Add doctor_availability table to existing database"""
    
    print("🔄 Starting database migration...")
    
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        # Create the new table
        print("📋 Creating doctor_availability table...")
        models.DoctorAvailability.__table__.create(engine, checkfirst=True)
        print("✅ Table created successfully")
        
        # Add default availability for existing doctors
        print("📅 Adding default availability for existing doctors...")
        db = SessionLocal()
        
        doctors = db.query(models.Doctor).all()
        
        if not doctors:
            print("⚠️  No doctors found in database")
            return
        
        for doctor in doctors:
            # Check if doctor already has availability
            existing = db.query(models.DoctorAvailability).filter(
                models.DoctorAvailability.doctor_id == doctor.id
            ).first()
            
            if existing:
                print(f"⚠️  Doctor {doctor.name} already has availability, skipping...")
                continue
            
            print(f"Adding default schedule for {doctor.name}...")
            
            # Add default Monday-Friday, 9 AM - 5 PM schedule
            for day in range(5):  # Monday to Friday
                availability = models.DoctorAvailability(
                    doctor_id=doctor.id,
                    day_of_week=day,
                    start_time="09:00 AM",
                    end_time="05:00 PM",
                    slot_duration=30
                )
                db.add(availability)
            
            print(f"✅ Added default schedule for {doctor.name}")
        
        db.commit()
        db.close()
        
        print("\n✅ Migration completed successfully!")
        print("\nNext steps:")
        print("1. Restart your backend server")
        print("2. Doctors can now customize their availability in their dashboard")
        print("3. Students will see real available slots when booking appointments")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure the backend server is not running")
        print("2. Check that DATABASE_URL is correctly set in your .env file")
        print("3. Ensure you have write permissions to the database file")

if __name__ == "__main__":
    migrate_database()