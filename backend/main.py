from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
import bcrypt
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from database import get_db, init_db
import models

load_dotenv()

app = FastAPI(title="CareConnect Health System API")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
security = HTTPBearer()

# Password hashing functions
def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    pwd_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)

def generate_aui_email(full_name: str) -> str:
    """Generate AUI email format: (first letter of first name).(last name)@aui.ma"""
    names = full_name.strip().split()
    if len(names) >= 2:
        first_initial = names[0][0].lower()
        last_name = names[-1].lower()
        return f"{first_initial}.{last_name}@aui.ma"
    return f"{names[0].lower()}@aui.ma"

# Pydantic Models
class UserLogin(BaseModel):
    username: str
    password: str

class UserRegister(BaseModel):
    username: str
    password: str
    full_name: str
    student_id: str  # Numbers only
    department: str  # SSE, SBA, SSAH
    major: str
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    year_level: Optional[str] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    department: Optional[str] = None
    major: Optional[str] = None
    year_level: Optional[str] = None

class EmergencyContactUpdate(BaseModel):
    name: str
    relationship: str
    phone: str
    email: Optional[str] = None

class MedicalEntryCreate(BaseModel):
    type: str  # allergy, medication, condition
    name: str
    description: Optional[str] = None
    severity: Optional[str] = None
    diagnosed_date: Optional[str] = None

class MedicalEntryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    is_active: Optional[bool] = None

class AppointmentCreate(BaseModel):
    doctor_id: int
    appointment_date: str
    appointment_time: str
    type: Optional[str] = "General Consultation"
    notes: Optional[str] = None

class EmergencyRequestCreate(BaseModel):
    type: str
    description: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

# Helper Functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        user = db.query(models.User).filter(models.User.username == username).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
        
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Routes
@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/")
def root():
    return {
        "message": "CareConnect Health System API",
        "version": "2.0.0",
        "status": "active"
    }

@app.post("/auth/register")
def register(user: UserRegister, db: Session = Depends(get_db)):
    # Check if username or student_id exists
    existing_user = db.query(models.User).filter(
        (models.User.username == user.username) | 
        (models.User.student_id == user.student_id)
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or Student ID already exists")
    
    # Validate department
    if user.department not in ["SSE", "SBA", "SSAH"]:
        raise HTTPException(status_code=400, detail="Invalid department. Must be SSE, SBA, or SSAH")
    
    # Generate AUI email
    email = generate_aui_email(user.full_name)
    
    # Create new user
    db_user = models.User(
        username=user.username,
        email=email,
        password_hash=hash_password(user.password),
        full_name=user.full_name,
        student_id=user.student_id,
        institution="Al Akhawayn University",
        department=user.department,
        major=user.major,
        academic_year="2025/2026",
        phone=user.phone,
        date_of_birth=datetime.strptime(user.date_of_birth, "%Y-%m-%d").date() if user.date_of_birth else None,
        gender=user.gender,
        year_level=user.year_level,
        role="student"
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    token = create_access_token({"sub": user.username})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": db_user.username,
            "full_name": db_user.full_name,
            "student_id": db_user.student_id,
            "email": db_user.email,
            "department": db_user.department,
            "major": db_user.major
        }
    }

@app.post("/auth/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": user.username})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": db_user.username,
            "full_name": db_user.full_name,
            "student_id": db_user.student_id,
            "email": db_user.email,
            "role": db_user.role
        }
    }

@app.get("/profile")
def get_profile(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    emergency_contact = db.query(models.EmergencyContact).filter(
        models.EmergencyContact.user_id == current_user.id
    ).first()
    
    return {
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "student_id": current_user.student_id,
        "institution": current_user.institution,
        "department": current_user.department,
        "major": current_user.major,
        "academic_year": current_user.academic_year,
        "year_level": current_user.year_level,
        "phone": current_user.phone,
        "date_of_birth": current_user.date_of_birth.isoformat() if current_user.date_of_birth else None,
        "gender": current_user.gender,
        "emergency_contact": {
            "name": emergency_contact.name,
            "relationship": emergency_contact.relationship,
            "phone": emergency_contact.phone,
            "email": emergency_contact.email
        } if emergency_contact else None
    }

@app.put("/profile/update")
def update_profile(
    updates: UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Update user fields
    if updates.full_name:
        current_user.full_name = updates.full_name
        # Regenerate email if name changed
        current_user.email = generate_aui_email(updates.full_name)
    
    if updates.phone:
        current_user.phone = updates.phone
    
    if updates.date_of_birth:
        current_user.date_of_birth = datetime.strptime(updates.date_of_birth, "%Y-%m-%d").date()
    
    if updates.gender:
        current_user.gender = updates.gender
    
    if updates.department:
        if updates.department not in ["SSE", "SBA", "SSAH"]:
            raise HTTPException(status_code=400, detail="Invalid department")
        current_user.department = updates.department
    
    if updates.major:
        current_user.major = updates.major
    
    if updates.year_level:
        current_user.year_level = updates.year_level
    
    current_user.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(current_user)
    
    return {"message": "Profile updated successfully", "email": current_user.email}

@app.put("/profile/emergency-contact")
def update_emergency_contact(
    contact: EmergencyContactUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing_contact = db.query(models.EmergencyContact).filter(
        models.EmergencyContact.user_id == current_user.id
    ).first()
    
    if existing_contact:
        existing_contact.name = contact.name
        existing_contact.relationship = contact.relationship
        existing_contact.phone = contact.phone
        existing_contact.email = contact.email
        existing_contact.updated_at = datetime.utcnow()
    else:
        new_contact = models.EmergencyContact(
            user_id=current_user.id,
            name=contact.name,
            relationship=contact.relationship,
            phone=contact.phone,
            email=contact.email
        )
        db.add(new_contact)
    
    db.commit()
    return {"message": "Emergency contact updated successfully"}

@app.get("/medical-records")
def get_medical_records(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    records = db.query(models.MedicalRecord).filter(
        models.MedicalRecord.user_id == current_user.id,
        models.MedicalRecord.is_active == True
    ).all()
    
    allergies = [r for r in records if r.type == "allergy"]
    medications = [r for r in records if r.type == "medication"]
    conditions = [r for r in records if r.type == "condition"]
    
    return {
        "allergies": [{"id": a.id, "name": a.name, "description": a.description, "severity": a.severity} for a in allergies],
        "medications": [{"id": m.id, "name": m.name, "description": m.description} for m in medications],
        "conditions": [{"id": c.id, "name": c.name, "description": c.description, "severity": c.severity} for c in conditions]
    }

@app.post("/medical-records/entry")
def add_medical_entry(
    entry: MedicalEntryCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if entry.type not in ["allergy", "medication", "condition"]:
        raise HTTPException(status_code=400, detail="Invalid entry type")
    
    db_entry = models.MedicalRecord(
        user_id=current_user.id,
        type=entry.type,
        name=entry.name,
        description=entry.description,
        severity=entry.severity,
        diagnosed_date=datetime.strptime(entry.diagnosed_date, "%Y-%m-%d").date() if entry.diagnosed_date else None
    )
    
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    
    return {"message": f"{entry.type.capitalize()} added successfully", "id": db_entry.id}

@app.put("/medical-records/{entry_id}")
def update_medical_entry(
    entry_id: int,
    updates: MedicalEntryUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    entry = db.query(models.MedicalRecord).filter(
        models.MedicalRecord.id == entry_id,
        models.MedicalRecord.user_id == current_user.id
    ).first()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Medical entry not found")
    
    if updates.name:
        entry.name = updates.name
    if updates.description:
        entry.description = updates.description
    if updates.severity:
        entry.severity = updates.severity
    if updates.is_active is not None:
        entry.is_active = updates.is_active
    
    entry.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Medical entry updated successfully"}

@app.delete("/medical-records/{entry_id}")
def delete_medical_entry(
    entry_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    entry = db.query(models.MedicalRecord).filter(
        models.MedicalRecord.id == entry_id,
        models.MedicalRecord.user_id == current_user.id
    ).first()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Medical entry not found")
    
    # Soft delete
    entry.is_active = False
    entry.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Medical entry deleted successfully"}

@app.get("/visits/all")
def get_all_visits(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    visits = db.query(models.Visit).filter(
        models.Visit.user_id == current_user.id
    ).order_by(models.Visit.visit_date.desc()).all()
    
    visit_list = []
    for visit in visits:
        doctor = db.query(models.Doctor).filter(models.Doctor.id == visit.doctor_id).first()
        visit_list.append({
            "id": visit.id,
            "date": visit.visit_date.isoformat(),
            "time_start": visit.time_start,
            "time_end": visit.time_end,
            "doctor_name": doctor.name if doctor else "Unknown",
            "doctor_specialty": doctor.specialty if doctor else "",
            "diagnosis": visit.diagnosis,
            "type": visit.type,
            "location": visit.location,
            "notes": visit.notes,
            "status": visit.status
        })
    
    stats = {
        "total": len(visits),
        "upcoming": len([v for v in visits if v.status == "upcoming"]),
        "completed": len([v for v in visits if v.status == "completed"]),
        "cancelled": len([v for v in visits if v.status == "cancelled"])
    }
    
    return {"visits": visit_list, "statistics": stats}

@app.post("/emergency")
def create_emergency_request(
    request: EmergencyRequestCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    emergency = models.EmergencyRequest(
        user_id=current_user.id,
        type=request.type,
        description=request.description,
        location=request.location,
        latitude=request.latitude,
        longitude=request.longitude,
        status="active",
        priority="high"
    )
    
    db.add(emergency)
    db.commit()
    db.refresh(emergency)
    
    return {
        "message": "Emergency request created",
        "emergency_id": emergency.id,
        "student_info": {
            "name": current_user.full_name,
            "student_id": current_user.student_id,
            "department": current_user.department
        }
    }

@app.get("/doctors")
def get_doctors(db: Session = Depends(get_db)):
    doctors = db.query(models.Doctor).filter(models.Doctor.is_available == True).all()
    return [
        {
            "id": doctor.id,
            "name": doctor.name,
            "specialty": doctor.specialty,
            "rating": doctor.rating,
            "reviews": doctor.reviews_count,
            "avatar": doctor.avatar
        }
        for doctor in doctors
    ]

# ============================================
# CHATBOT ENDPOINTS
# ============================================

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    user_context: Optional[dict] = None

class ChatResponse(BaseModel):
    reply: str
    conversation_id: str
    model: Optional[str] = None
    mode: Optional[str] = None
    action_detected: Optional[bool] = False
    action_type: Optional[str] = None

@app.post("/chat/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    AI Chatbot endpoint - provides guidance and information
    
    The chatbot GUIDES users but does NOT perform actions.
    It explains how to use features and directs to appropriate pages.
    """
    try:
        from chatbot import ai_reply
        
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or f"conv_{datetime.utcnow().timestamp()}"
        
        # Get AI response
        response = ai_reply(
            message=request.message,
            conversation_id=conversation_id,
            user_context=request.user_context
        )
        
        return ChatResponse(
            reply=response.get("reply", "I'm having trouble responding right now."),
            conversation_id=response.get("conversation_id", conversation_id),
            model=response.get("model"),
            mode=response.get("mode"),
            action_detected=response.get("action_detected", False),
            action_type=response.get("action_type")
        )
    
    except Exception as e:
        print(f"❌ Chat endpoint error: {e}")
        return ChatResponse(
            reply="I apologize, but I'm having technical difficulties. Please try again or contact support.",
            conversation_id=request.conversation_id or "error",
            mode="error"
        )

@app.post("/chat/clear/{conversation_id}")
async def clear_chat(conversation_id: str):
    """Clear conversation history for a specific conversation"""
    try:
        from chatbot import clear_conversation
        success = clear_conversation(conversation_id)
        return {
            "success": success,
            "message": "Conversation cleared" if success else "Conversation not found"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/analyze-urgency")
async def analyze_urgency_endpoint(request: ChatRequest):
    """Analyze if a message indicates an emergency"""
    try:
        from chatbot import analyze_urgency
        result = analyze_urgency(request.message)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/help/{topic}")
async def get_help(topic: str):
    """Get quick help for common topics"""
    try:
        from chatbot import get_quick_help
        help_text = get_quick_help(topic)
        return {"topic": topic, "help": help_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)