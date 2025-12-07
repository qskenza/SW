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

# Import chatbot
try:
    from chatbot import ai_reply
    CHATBOT_AVAILABLE = True
except ImportError:
    CHATBOT_AVAILABLE = False
    print("⚠️ Chatbot module not found. Chat features will be disabled.")

load_dotenv()

app = FastAPI(title="CareConnect Health System API")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les domaines autorisés
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
    """Hash a password using bcrypt"""
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    pwd_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)

# Models
class UserLogin(BaseModel):
    username: str
    password: str

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    student_id: str
    institution: str
    program: str

class AppointmentCreate(BaseModel):
    doctor_id: str
    date: str
    time: str
    type: str = "General Consultation"

class MedicalEntry(BaseModel):
    type: str  # "allergy", "medication", "condition"
    name: str
    description: Optional[str] = None

class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class EmergencyRequest(BaseModel):
    type: str
    description: str
    location: Optional[str] = None

# Simulated Database (In production, use a real database)
users_db = {
    "alexandra": {
        "username": "alexandra",
        "email": "alexandra@example.com",
        "password": hash_password("password123"),
        "full_name": "Alexandra Miller",
        "student_id": "S2023001",
        "institution": "Greenwood High School",
        "program": "Biology",
        "role": "student"
    },
    "admin": {
        "username": "admin",
        "email": "admin@careconnect.com",
        "password": hash_password("admin123"),
        "full_name": "Admin User",
        "role": "admin"
    }
}

appointments_db = []
medical_records_db = {}
emergency_requests_db = []

# Helper Functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        print(f"🔍 Received token: {token[:20]}..." if len(token) > 20 else f"🔍 Received token: {token}")
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        
        print(f"✅ Token decoded successfully. Username: {username}")
        
        if username is None or username not in users_db:
            print(f"❌ User not found: {username}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        print(f"✅ User authenticated: {username}")
        return users_db[username]
        
    except ExpiredSignatureError:
        print("❌ Token expired")
        raise HTTPException(status_code=401, detail="Token expired")
        
    except InvalidTokenError as e:
        print(f"❌ Invalid token: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
        
    except Exception as e:
        print(f"❌ Auth error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

# Routes
@app.get("/")
def root():
    return {
        "message": "CareConnect Health System API",
        "version": "1.0.0",
        "status": "active"
    }

@app.get("/test")
def test_endpoint():
    """Test endpoint without authentication"""
    return {
        "status": "success",
        "message": "API is working correctly",
        "test_users": {
            "student": {"username": "alexandra", "password": "password123"},
            "admin": {"username": "admin", "password": "admin123"}
        },
        "instructions": "Use /auth/login to get a token, then use it in Authorization header"
    }

@app.post("/auth/register")
def register(user: UserRegister):
    if user.username in users_db:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    users_db[user.username] = {
        "username": user.username,
        "email": user.email,
        "password": hash_password(user.password),
        "full_name": user.full_name,
        "student_id": user.student_id,
        "institution": user.institution,
        "program": user.program,
        "role": "student"
    }
    
    medical_records_db[user.username] = {
        "allergies": [],
        "medications": [],
        "conditions": [],
        "visits": []
    }
    
    token = create_access_token({"sub": user.username})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": user.username,
            "full_name": user.full_name,
            "student_id": user.student_id
        }
    }

@app.post("/auth/login")
def login(user: UserLogin):
    if user.username not in users_db:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    db_user = users_db[user.username]
    if not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": user.username})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": db_user["username"],
            "full_name": db_user["full_name"],
            "role": db_user.get("role", "student")
        }
    }

@app.get("/profile")
def get_profile(current_user: dict = Depends(get_current_user)):
    try:
        print(f"✅ User authenticated: {current_user.get('username')}")
        return {
            "username": current_user["username"],
            "email": current_user["email"],
            "full_name": current_user["full_name"],
            "student_id": current_user.get("student_id"),
            "institution": current_user.get("institution"),
            "program": current_user.get("program")
        }
    except Exception as e:
        print(f"❌ Error in get_profile: {e}")
        raise HTTPException(status_code=500, detail=f"Profile error: {str(e)}")

@app.get("/medical-records")
def get_medical_records(current_user: dict = Depends(get_current_user)):
    try:
        username = current_user["username"]
        print(f"✅ Fetching medical records for: {username}")
        
        if username not in medical_records_db:
            medical_records_db[username] = {
                "allergies": ["Peanuts", "Penicillin"],
                "medications": ["Inhaler (Albuterol)"],
                "conditions": ["Asthma", "Seasonal Allergies"],
                "visits": [
                    {
                        "date": "2023-11-15",
                        "diagnosis": "Seasonal Allergies",
                        "doctor": "Dr. Bob Johnston",
                        "status": "Completed"
                    },
                    {
                        "date": "2024-01-20",
                        "diagnosis": "Minor Sprain (Active)",
                        "doctor": "Dr. Alice Smith",
                        "status": "Active"
                    },
                    {
                        "date": "2024-03-01",
                        "diagnosis": "Routine Check-up",
                        "doctor": "Dr. Elena Rodriguez",
                        "status": "Completed"
                    }
                ]
            }
        return medical_records_db[username]
    except Exception as e:
        print(f"❌ Error in get_medical_records: {e}")
        raise HTTPException(status_code=500, detail=f"Medical records error: {str(e)}")

@app.post("/medical-records/entry")
def add_medical_entry(entry: MedicalEntry, current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    if username not in medical_records_db:
        medical_records_db[username] = {"allergies": [], "medications": [], "conditions": [], "visits": []}
    
    if entry.type == "allergy":
        medical_records_db[username]["allergies"].append(entry.name)
    elif entry.type == "medication":
        medical_records_db[username]["medications"].append(entry.name)
    elif entry.type == "condition":
        medical_records_db[username]["conditions"].append(entry.name)
    
    return {"message": f"{entry.type.capitalize()} added successfully", "data": entry}

@app.get("/appointments")
def get_appointments(current_user: dict = Depends(get_current_user)):
    user_appointments = [apt for apt in appointments_db if apt["username"] == current_user["username"]]
    return user_appointments

@app.post("/appointments")
def create_appointment(appointment: AppointmentCreate, current_user: dict = Depends(get_current_user)):
    new_appointment = {
        "id": len(appointments_db) + 1,
        "username": current_user["username"],
        "doctor_id": appointment.doctor_id,
        "date": appointment.date,
        "time": appointment.time,
        "type": appointment.type,
        "status": "upcoming",
        "created_at": datetime.utcnow().isoformat()
    }
    appointments_db.append(new_appointment)
    return {"message": "Appointment created successfully", "appointment": new_appointment}

@app.delete("/appointments/{appointment_id}")
def cancel_appointment(appointment_id: int, current_user: dict = Depends(get_current_user)):
    for apt in appointments_db:
        if apt["id"] == appointment_id and apt["username"] == current_user["username"]:
            appointments_db.remove(apt)
            return {"message": "Appointment cancelled successfully"}
    raise HTTPException(status_code=404, detail="Appointment not found")

@app.get("/doctors")
def get_doctors():
    return [
        {
            "id": "dr_chen",
            "name": "Dr. Sarah Chen",
            "specialty": "General Practitioner, Pediatrics",
            "rating": 4.8,
            "reviews": 127,
            "avatar": "SC"
        },
        {
            "id": "dr_carter",
            "name": "Dr. Emily Carter",
            "specialty": "Pediatrician",
            "rating": 4.9,
            "reviews": 89,
            "avatar": "EC"
        },
        {
            "id": "dr_rodriguez",
            "name": "Dr. Elena Rodriguez",
            "specialty": "Campus Doctor",
            "rating": 4.7,
            "reviews": 156,
            "avatar": "ER"
        }
    ]

@app.post("/emergency")
def create_emergency_request(request: EmergencyRequest, current_user: dict = Depends(get_current_user)):
    emergency = {
        "id": len(emergency_requests_db) + 1,
        "username": current_user["username"],
        "type": request.type,
        "description": request.description,
        "location": request.location,
        "status": "active",
        "created_at": datetime.utcnow().isoformat()
    }
    emergency_requests_db.append(emergency)
    return {"message": "Emergency request created", "emergency": emergency}

@app.get("/dashboard/stats")
def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    records = medical_records_db.get(username, {"allergies": [], "medications": [], "conditions": [], "visits": []})
    user_appointments = [apt for apt in appointments_db if apt["username"] == username]
    
    return {
        "allergies_count": len(records["allergies"]),
        "medications_count": len(records["medications"]),
        "conditions_count": len(records["conditions"]),
        "visits_count": len(records["visits"]),
        "upcoming_appointments": len([apt for apt in user_appointments if apt["status"] == "upcoming"])
    }

# Chatbot Routes
@app.post("/chat/")
def chat(data: ChatMessage):
    """Send a message to the AI chatbot"""
    if not CHATBOT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Chatbot service unavailable")
    
    try:
        conversation_id = data.conversation_id or "default"
        response = ai_reply(
            message=data.message,
            conversation_id=conversation_id
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chatbot error: {str(e)}")

@app.get("/chat/health")
def chatbot_health():
    """Check chatbot service status"""
    return {
        "chatbot_available": CHATBOT_AVAILABLE,
        "service": "CareConnect Health Assistant",
        "status": "operational" if CHATBOT_AVAILABLE else "disabled"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)