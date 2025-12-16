from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Float, Date, Time
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
    student_id = Column(String(50), unique=True, index=True, nullable=False)
    institution = Column(String(100), default="Al Akhawayn University")
    department = Column(String(10))
    major = Column(String(100))
    academic_year = Column(String(20), default="2025/2026")
    year_level = Column(String(20))
    phone = Column(String(20))
    date_of_birth = Column(Date)
    gender = Column(String(20))
    role = Column(String(20), default="student")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    medical_records = orm_relationship("MedicalRecord", back_populates="user", cascade="all, delete-orphan")
    appointments = orm_relationship("Appointment", back_populates="user", cascade="all, delete-orphan")
    emergency_requests = orm_relationship("EmergencyRequest", back_populates="user", cascade="all, delete-orphan")
    emergency_contact = orm_relationship("EmergencyContact", back_populates="user", uselist=False, cascade="all, delete-orphan")
    doctor_profile = orm_relationship("Doctor", back_populates="user", uselist=False)
    nurse_profile = orm_relationship("Nurse", back_populates="user", uselist=False)


class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    relationship = Column(String(50), nullable=False)
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
    type = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    severity = Column(String(20))
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
    type = Column(String(50))
    location = Column(String(100))
    notes = Column(Text)
    status = Column(String(20), default="completed")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = orm_relationship("User")
    doctor = orm_relationship("Doctor")


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=True)
    name = Column(String(100), nullable=False)
    license_number = Column(String(50), unique=True, nullable=True)
    specialty = Column(String(100))
    email = Column(String(100), unique=True)
    phone = Column(String(20))
    rating = Column(Float, default=0.0)
    reviews_count = Column(Integer, default=0)
    avatar = Column(String(10))
    is_available = Column(Boolean, default=True)
    professional_experience = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = orm_relationship("User", back_populates="doctor_profile")
    appointments = orm_relationship("Appointment", back_populates="doctor")
    availability_slots = orm_relationship("DoctorAvailability", back_populates="doctor", cascade="all, delete-orphan")


class DoctorAvailability(Base):
    """Doctor's availability schedule"""
    __tablename__ = "doctor_availability"
    
    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = Column(String(10), nullable=False)  # e.g., "09:00 AM"
    end_time = Column(String(10), nullable=False)    # e.g., "05:00 PM"
    slot_duration = Column(Integer, default=30)      # Duration in minutes
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    doctor = orm_relationship("Doctor", back_populates="availability_slots")


class Nurse(Base):
    __tablename__ = "nurses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True)
    phone = Column(String(20))
    avatar = Column(String(10))
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = orm_relationship("User", back_populates="nurse_profile")


class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    appointment_date = Column(Date, nullable=False)
    appointment_time = Column(String(10))
    type = Column(String(50), default="General Consultation")
    location = Column(String(100))
    status = Column(String(20), default="upcoming")
    notes = Column(Text)
    can_reschedule = Column(Boolean, default=True)
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
    status = Column(String(20), default="active")
    priority = Column(String(20), default="high")
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    
    # Relationships
    user = orm_relationship("User", back_populates="emergency_requests")