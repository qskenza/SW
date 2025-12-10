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
    
    # Seed initial data
    seed_db()

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
            email="a.miller@aui.ma",  # ✅ CHANGED: AUI email format
            password_hash=hash_password("password123"),
            full_name="Alexandra Miller",
            student_id="2023001",  # ✅ CHANGED: Numbers only (removed "S")
            institution="Al Akhawayn University",  # ✅ CHANGED: AUI
            department="SSE",  # ✅ ADDED: Department
            major="Computer Science",  # ✅ CHANGED: From "program" to "major"
            academic_year="2025/2026",  # ✅ ADDED: Academic year
            year_level="junior",  # ✅ ADDED: Year level
            phone="+212 612-345678",  # ✅ ADDED: Phone
            date_of_birth=date(2002, 5, 10),  # ✅ ADDED: Date of birth
            gender="female",  # ✅ ADDED: Gender
            role="student"
        )
        db.add(alexandra)
        db.flush()
        
        # ✅ ADDED: Emergency contact for Alexandra
        emergency_contact = models.EmergencyContact(
            user_id=alexandra.id,
            name="Jane Miller",
            relationship="Mother",
            phone="+1 555-123-4567",
            email="jane.miller@example.com"
        )
        db.add(emergency_contact)
        
        # ✅ ADDED: Medical records for Alexandra
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
                email="sarah.chen@aui.ma",  # ✅ CHANGED: AUI email
                phone="0535-86-0101",  # ✅ CHANGED: Moroccan format
                rating=4.8,  # ✅ CHANGED: Decimal rating instead of integer
                reviews_count=127,
                avatar="SC"
            ),
            models.Doctor(
                name="Dr. Emily Carter",
                specialty="Pediatrician",
                email="emily.carter@aui.ma",  # ✅ CHANGED: AUI email
                phone="0535-86-0102",  # ✅ CHANGED: Moroccan format
                rating=4.9,  # ✅ CHANGED: Decimal rating
                reviews_count=89,
                avatar="EC"
            ),
            models.Doctor(
                name="Dr. Elena Rodriguez",
                specialty="Campus Doctor",
                email="elena.rodriguez@aui.ma",  # ✅ CHANGED: AUI email
                phone="0535-86-0103",  # ✅ CHANGED: Moroccan format
                rating=4.7,  # ✅ CHANGED: Decimal rating
                reviews_count=156,
                avatar="ER"
            )
        ]
        
        for doctor in doctors:
            db.add(doctor)
        
        # ✅ ADD DEFAULT AVAILABILITY FOR DOCTORS
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
        
        db.flush()
        
        # ✅ ADDED: Sample visits for Alexandra
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
            email="admin@aui.ma",  # ✅ CHANGED: AUI email
            password_hash=hash_password("admin123"),
            full_name="Admin User",
            student_id="0000000",  # ✅ ADDED: Required field
            institution="Al Akhawayn University",  # ✅ CHANGED: AUI
            role="admin"
        )
        db.add(admin)
        
        db.commit()
        print("✅ Database seeded successfully")
        print("📧 Alexandra's email: a.miller@aui.ma")  # ✅ ADDED: Confirmation
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Initializing database...")
    init_db()