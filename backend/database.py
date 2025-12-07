from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from typing import Generator
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./careconnect.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

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
    from models import Base
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")

# Seed initial data
def seed_db():
    """Seed database with initial data"""
    from models import User, Doctor
    import bcrypt
    
    def hash_password(password: str) -> str:
        pwd_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(pwd_bytes, salt)
        return hashed.decode('utf-8')
    
    db = SessionLocal()
    
    try:
        # Check if data already exists
        if db.query(User).first():
            print("⚠️  Database already seeded")
            return
        
        # Create default users
        default_users = [
            User(
                username="alexandra",
                email="alexandra@example.com",
                password_hash=hash_password("password123"),
                full_name="Alexandra Miller",
                student_id="S2023001",
                institution="Greenwood High School",
                program="Biology",
                role="student"
            ),
            User(
                username="admin",
                email="admin@careconnect.com",
                password_hash=hash_password("admin123"),
                full_name="Admin User",
                role="admin"
            )
        ]
        
        for user in default_users:
            db.add(user)
        
        # Create default doctors
        default_doctors = [
            Doctor(
                name="Dr. Sarah Chen",
                specialty="General Practitioner, Pediatrics",
                email="sarah.chen@careconnect.com",
                phone="555-0101",
                rating=48,
                reviews_count=127,
                avatar="SC"
            ),
            Doctor(
                name="Dr. Emily Carter",
                specialty="Pediatrician",
                email="emily.carter@careconnect.com",
                phone="555-0102",
                rating=49,
                reviews_count=89,
                avatar="EC"
            ),
            Doctor(
                name="Dr. Elena Rodriguez",
                specialty="Campus Doctor",
                email="elena.rodriguez@careconnect.com",
                phone="555-0103",
                rating=47,
                reviews_count=156,
                avatar="ER"
            )
        ]
        
        for doctor in default_doctors:
            db.add(doctor)
        
        db.commit()
        print("✅ Database seeded successfully")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Seeding database...")
    seed_db()