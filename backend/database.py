from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL - use SQLite for simplicity, can be changed to PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./careconnect.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get DB session
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database
def init_db():
    """Create all tables in the database"""
    import models
    models.Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")

    # Run migrations
    run_migrations()

    # Seed initial data
    seed_db()

def run_migrations():
    """Run database migrations to update schema"""
    from sqlalchemy import text
    db = SessionLocal()
    try:
        # Migration 1: Add professional_experience column to doctors table
        try:
            # Check if column exists
            result = db.execute(text("PRAGMA table_info(doctors)"))
            columns = [row[1] for row in result.fetchall()]

            if 'professional_experience' not in columns:
                print("🔄 Running migration: Adding professional_experience column to doctors table...")
                db.execute(text("ALTER TABLE doctors ADD COLUMN professional_experience TEXT"))
                db.commit()
                print("✅ Migration completed: professional_experience column added")
            else:
                print("✅ professional_experience column already exists")
        except Exception as e:
            print(f"⚠️  Migration warning: {e}")
            db.rollback()

        # Migration 2: Create nurses table if it doesn't exist
        try:
            result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='nurses'"))
            table_exists = result.fetchone() is not None

            if not table_exists:
                print("🔄 Running migration: Creating nurses table...")
                db.execute(text("""
                    CREATE TABLE nurses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER UNIQUE,
                        name VARCHAR(100) NOT NULL,
                        email VARCHAR(100) UNIQUE,
                        phone VARCHAR(20),
                        avatar VARCHAR(10),
                        is_available BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """))
                db.commit()
                print("✅ Migration completed: nurses table created")
            else:
                print("✅ nurses table already exists")
        except Exception as e:
            print(f"⚠️  Migration warning: {e}")
            db.rollback()
    finally:
        db.close()

def seed_db():
    """Seed database with initial data"""
    import models
    import bcrypt
    from datetime import date
    
    def hash_password(password: str) -> str:
        pwd_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(pwd_bytes, salt)
        return hashed.decode('utf-8')
    
    db = SessionLocal()
    
    try:
        # Check if data already exists
        if db.query(models.User).first():
            print("⚠️  Database already seeded")
            return
        
        # Create default user - Alexandra Miller
        alexandra = models.User(
            username="alexandra",
            email="a.miller@aui.ma",
            password_hash=hash_password("password123"),
            full_name="Alexandra Miller",
            student_id="2023001",
            institution="Al Akhawayn University",
            department="SSE",
            major="Computer Science",
            academic_year="2025/2026",
            year_level="junior",
            phone="+212 612-345678",
            date_of_birth=date(2002, 5, 10),
            gender="female",
            role="student"
        )
        db.add(alexandra)
        db.flush()
        
        # Emergency contact for Alexandra
        emergency_contact = models.EmergencyContact(
            user_id=alexandra.id,
            name="Jane Miller",
            relationship="Mother",
            phone="+1 555-123-4567",
            email="jane.miller@example.com"
        )
        db.add(emergency_contact)
        
        # Medical records for Alexandra
        allergies = [
            models.MedicalRecord(
                user_id=alexandra.id,
                type="allergy",
                name="Peanuts",
                severity="severe"
            ),
            models.MedicalRecord(
                user_id=alexandra.id,
                type="allergy",
                name="Penicillin",
                severity="moderate"
            )
        ]
        
        medications = [
            models.MedicalRecord(
                user_id=alexandra.id,
                type="medication",
                name="Inhaler (Albuterol)",
                description="As needed"
            )
        ]
        
        conditions = [
            models.MedicalRecord(
                user_id=alexandra.id,
                type="condition",
                name="Asthma",
                severity="moderate"
            ),
            models.MedicalRecord(
                user_id=alexandra.id,
                type="condition",
                name="Seasonal Allergies",
                severity="mild"
            )
        ]
        
        for record in allergies + medications + conditions:
            db.add(record)
        
        # Create default doctors
        doctors = [
            models.Doctor(
                name="Dr. Sarah Chen",
                specialty="General Practitioner, Pediatrics",
                email="sarah.chen@aui.ma",
                phone="0535-86-0101",
                rating=4.8,
                reviews_count=127,
                avatar="SC"
            ),
            models.Doctor(
                name="Dr. Emily Carter",
                specialty="Pediatrician",
                email="emily.carter@aui.ma",
                phone="0535-86-0102",
                rating=4.9,
                reviews_count=89,
                avatar="EC"
            ),
            models.Doctor(
                name="Dr. Elena Rodriguez",
                specialty="Campus Doctor",
                email="elena.rodriguez@aui.ma",
                phone="0535-86-0103",
                rating=4.7,
                reviews_count=156,
                avatar="ER"
            )
        ]
        
        for doctor in doctors:
            db.add(doctor)
        
        # ✅ FIX: Commit doctors first so they get IDs
        db.commit()
        print("✅ Doctors created successfully")
        
        # Now create availability schedules with valid doctor IDs
        print("📅 Creating default doctor availability schedules...")
        
        # Dr. Sarah Chen - Available Mon-Fri, 9 AM - 5 PM
        for day in range(5):  # Monday to Friday (0-4)
            availability = models.DoctorAvailability(
                doctor_id=doctors[0].id,
                day_of_week=day,
                start_time="09:00 AM",
                end_time="05:00 PM",
                slot_duration=30
            )
            db.add(availability)
        
        # Dr. Emily Carter - Available Mon-Thu, 10 AM - 4 PM
        for day in range(4):  # Monday to Thursday (0-3)
            availability = models.DoctorAvailability(
                doctor_id=doctors[1].id,
                day_of_week=day,
                start_time="10:00 AM",
                end_time="04:00 PM",
                slot_duration=30
            )
            db.add(availability)
        
        # Dr. Elena Rodriguez - Available Tue-Sat, 8 AM - 3 PM
        for day in [1, 2, 3, 4, 5]:  # Tuesday to Saturday (1-5)
            availability = models.DoctorAvailability(
                doctor_id=doctors[2].id,
                day_of_week=day,
                start_time="08:00 AM",
                end_time="03:00 PM",
                slot_duration=45  # 45-minute slots
            )
            db.add(availability)
        
        db.commit()
        print("✅ Doctor availability schedules created")
        
        # Sample visits for Alexandra
        visits = [
            models.Visit(
                user_id=alexandra.id,
                doctor_id=doctors[2].id,  # Dr. Elena Rodriguez
                visit_date=date(2024, 3, 1),
                time_start="2:00 PM",
                time_end="2:30 PM",
                diagnosis="Routine Check-up",
                type="General Consultation",
                location="Room 204",
                notes="Annual physical examination completed. All vital signs normal. Continue current medication regimen for asthma management. Next check-up recommended in 12 months.",
                status="completed"
            ),
            models.Visit(
                user_id=alexandra.id,
                doctor_id=doctors[0].id,  # Dr. Sarah Chen
                visit_date=date(2024, 1, 20),
                time_start="11:00 AM",
                time_end="11:45 AM",
                diagnosis="Minor Ankle Sprain",
                type="Injury Assessment",
                location="Room 101",
                notes="Grade I ankle sprain from sports activity. RICE protocol recommended. Prescribed anti-inflammatory medication. Follow-up in 2 weeks showed complete recovery.",
                status="completed"
            ),
            models.Visit(
                user_id=alexandra.id,
                doctor_id=doctors[1].id,  # Dr. Emily Carter
                visit_date=date(2023, 11, 15),
                time_start="3:30 PM",
                time_end="4:00 PM",
                diagnosis="Seasonal Allergies",
                type="General Consultation",
                location="Room 302",
                notes="Patient presented with typical seasonal allergy symptoms. Prescribed antihistamines. Advised to avoid known allergens and use air purifier. Symptoms resolved within one week.",
                status="completed"
            )
        ]
        
        for visit in visits:
            db.add(visit)
        
        # Create admin user
        admin = models.User(
            username="admin",
            email="admin@aui.ma",
            password_hash=hash_password("admin123"),
            full_name="Admin User",
            student_id="0000000",
            institution="Al Akhawayn University",
            role="admin"
        )
        db.add(admin)
        
        db.commit()
        print("✅ Database seeded successfully")
        print("📧 Alexandra's email: a.miller@aui.ma")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
        raise  # Re-raise to see full traceback
    finally:
        db.close()

if __name__ == "__main__":
    print("Initializing database...")
    init_db()