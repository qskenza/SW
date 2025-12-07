from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship as orm_relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    student_id = Column(String(50), unique=True, index=True, nullable=False)  # For students: numeric, for doctors: D + timestamp
    institution = Column(String(100), default="Al Akhawayn University")
    department = Column(String(10))  # SSE, SBA, SSAH (for students)
    major = Column(String(100))  # Major for students, specialty for doctors
    academic_year = Column(String(20), default="2025/2026")
    year_level = Column(String(20))  # freshman, sophomore, junior, senior
    phone = Column(String(20))
    date_of_birth = Column(Date)
    gender = Column(String(20))
    role = Column(String(20), default="student")  # student, doctor, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    medical_records = orm_relationship("MedicalRecord", back_populates="user", cascade="all, delete-orphan")
    appointments = orm_relationship("Appointment", back_populates="user", cascade="all, delete-orphan")
    emergency_requests = orm_relationship("EmergencyRequest", back_populates="user", cascade="all, delete-orphan")
    emergency_contact = orm_relationship("EmergencyContact", back_populates="user", uselist=False, cascade="all, delete-orphan")
    doctor_profile = orm_relationship("Doctor", back_populates="user", uselist=False)


class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    relationship = Column(String(50), nullable=False)  # This is a column, not SQLAlchemy relationship
    phone = Column(String(20), nullable=False)
    email = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = orm_relationship("User", back_populates="emergency_contact")


class MedicalRecord(Base):
    __tablename__ = "medical_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(20), nullable=False)  # allergy, medication, condition
    name = Column(String(100), nullable=False)
    description = Column(Text)
    severity = Column(String(20))  # mild, moderate, severe
    diagnosed_date = Column(Date)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = orm_relationship("User", back_populates="medical_records")


class Visit(Base):
    __tablename__ = "visits"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    visit_date = Column(Date, nullable=False)
    time_start = Column(String(10))
    time_end = Column(String(10))
    diagnosis = Column(String(200))
    type = Column(String(50))  # General Consultation, Follow-up, Emergency, etc.
    location = Column(String(100))
    notes = Column(Text)
    status = Column(String(20), default="completed")  # upcoming, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = orm_relationship("User")
    doctor = orm_relationship("Doctor")


class Doctor(Base):
    __tablename__ = "doctors"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=True)  # Nullable for seeded doctors
    name = Column(String(100), nullable=False)
    license_number = Column(String(50), unique=True, nullable=True)  # Nullable for seeded doctors
    specialty = Column(String(100))
    email = Column(String(100), unique=True)
    phone = Column(String(20))
    rating = Column(Float, default=0.0)
    reviews_count = Column(Integer, default=0)
    avatar = Column(String(10))
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = orm_relationship("User", back_populates="doctor_profile")
    appointments = orm_relationship("Appointment", back_populates="doctor")


class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    appointment_date = Column(DateTime, nullable=False)
    appointment_time = Column(String(10))
    type = Column(String(50), default="General Consultation")
    location = Column(String(100))
    status = Column(String(20), default="upcoming")  # upcoming, completed, cancelled
    notes = Column(Text)
    can_reschedule = Column(Boolean, default=True)  # Based on 12-hour rule
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = orm_relationship("User", back_populates="appointments")
    doctor = orm_relationship("Doctor", back_populates="appointments")


class EmergencyRequest(Base):
    __tablename__ = "emergency_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(50))
    description = Column(Text, nullable=False)
    location = Column(String(200))
    latitude = Column(Float)
    longitude = Column(Float)
    status = Column(String(20), default="active")  # active, responded, resolved
    priority = Column(String(20), default="high")  # low, medium, high, critical
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    
    # Relationships
    user = orm_relationship("User", back_populates="emergency_requests")