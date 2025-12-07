from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    student_id = Column(String(50), unique=True, index=True)
    institution = Column(String(100))
    program = Column(String(100))
    role = Column(String(20), default="student")  # student, doctor, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    medical_records = relationship("MedicalRecord", back_populates="user")
    appointments = relationship("Appointment", back_populates="user")
    emergency_requests = relationship("EmergencyRequest", back_populates="user")
    chat_conversations = relationship("ChatConversation", back_populates="user")

class MedicalRecord(Base):
    __tablename__ = "medical_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(20))  # allergy, medication, condition, visit
    name = Column(String(100))
    description = Column(Text)
    diagnosis = Column(String(200))
    doctor_name = Column(String(100))
    visit_date = Column(DateTime)
    status = Column(String(20), default="active")  # active, resolved, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="medical_records")

class Doctor(Base):
    __tablename__ = "doctors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    specialty = Column(String(100))
    email = Column(String(100), unique=True)
    phone = Column(String(20))
    rating = Column(Integer, default=0)
    reviews_count = Column(Integer, default=0)
    avatar = Column(String(10))
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    appointments = relationship("Appointment", back_populates="doctor")

class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    appointment_date = Column(DateTime, nullable=False)
    appointment_time = Column(String(10))
    type = Column(String(50), default="General Consultation")
    status = Column(String(20), default="upcoming")  # upcoming, completed, cancelled
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")

class EmergencyRequest(Base):
    __tablename__ = "emergency_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(50))
    description = Column(Text, nullable=False)
    location = Column(String(200))
    status = Column(String(20), default="active")  # active, responded, resolved
    priority = Column(String(20), default="high")  # low, medium, high, critical
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="emergency_requests")

class ChatConversation(Base):
    __tablename__ = "chat_conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    conversation_id = Column(String(100), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="chat_conversations")
    messages = relationship("ChatMessage", back_populates="conversation")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("chat_conversations.id"), nullable=False)
    role = Column(String(20))  # user, assistant, system
    content = Column(Text, nullable=False)
    tokens_used = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("ChatConversation", back_populates="messages")