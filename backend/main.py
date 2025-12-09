from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta, date
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
import bcrypt
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from database import get_db
import models

load_dotenv()

app = FastAPI(title="CareConnect Health System API")

# ---------------------------------------------------------
# CORS CONFIG
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# SECURITY
# ---------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
security = HTTPBearer()


# ---------------------------------------------------------
# PASSWORD HASHING
# ---------------------------------------------------------
def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


def generate_aui_email(full_name: str) -> str:
    """Generate AUI email: (first letter).(lastname)@aui.ma"""
    names = full_name.strip().split()
    if len(names) >= 2:
        return f"{names[0][0].lower()}.{names[-1].lower()}@aui.ma"
    return f"{names[0].lower()}@aui.ma"


# ---------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------
class AppointmentCreate(BaseModel):
    doctor_id: int
    appointment_date: str
    appointment_time: str
    type: str = "General Consultation"
    notes: Optional[str] = None


class AppointmentUpdate(BaseModel):
    appointment_date: Optional[str] = None
    appointment_time: Optional[str] = None
    type: Optional[str] = None
    notes: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserRegister(BaseModel):
    username: str
    password: str
    full_name: str
    student_id: str  # For students: numeric ID, for doctors: license number or generated
    role: str = "student"  # student or doctor
    # Student fields
    department: Optional[str] = None
    major: Optional[str] = None
    year_level: Optional[str] = None
    # Doctor fields
    license_number: Optional[str] = None
    specialization: Optional[str] = None
    # Common fields
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None


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
    type: str
    name: str
    description: Optional[str] = None
    severity: Optional[str] = None
    diagnosed_date: Optional[str] = None


class MedicalEntryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    is_active: Optional[bool] = None


class EmergencyRequestCreate(BaseModel):
    type: str
    description: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


# ---------------------------------------------------------
# TOKEN & AUTH
# ---------------------------------------------------------
def create_access_token(data: dict):
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=24)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")

        user = db.query(models.User).filter(
            models.User.username == username
        ).first()

        if not user:
            raise HTTPException(401, "User not found")

        return user

    except ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except InvalidTokenError:
        raise HTTPException(401, "Invalid token")


# ---------------------------------------------------------
# ROOT
# ---------------------------------------------------------
@app.get("/")
def root():
    return {
        "message": "CareConnect Health System API",
        "version": "2.0.0",
        "status": "active"
    }


# ---------------------------------------------------------
# AUTH
# ---------------------------------------------------------
@app.post("/auth/register")
def register(user: UserRegister, db: Session = Depends(get_db)):
    # Check if username already exists
    existing_user = db.query(models.User).filter(
        models.User.username == user.username
    ).first()
    
    if existing_user:
        raise HTTPException(400, "Username already exists")

    # For students, check if student_id already exists
    if user.role == "student":
        existing_student = db.query(models.User).filter(
            models.User.student_id == user.student_id
        ).first()
        if existing_student:
            raise HTTPException(400, "Student ID already exists")

    # Validate role-specific fields
    if user.role == "student":
        if not user.department or not user.major:
            raise HTTPException(400, "Department and Major required for students")
        if user.department not in ["SSE", "SBA", "SSAH"]:
            raise HTTPException(400, "Invalid department. Must be SSE, SBA, or SSAH")
    elif user.role == "doctor":
        if not user.license_number or not user.specialization:
            raise HTTPException(400, "License number and Specialization required for doctors")
        # Check if license number already exists
        existing_doctor = db.query(models.Doctor).filter(
            models.Doctor.license_number == user.license_number
        ).first()
        if existing_doctor:
            raise HTTPException(400, "License number already registered")
    else:
        raise HTTPException(400, "Invalid role. Must be 'student' or 'doctor'")

    # Generate AUI email
    email = generate_aui_email(user.full_name)
    
    # Check if email already exists and make it unique if needed
    base_email = email
    counter = 1
    while db.query(models.User).filter(models.User.email == email).first():
        name_parts = base_email.split('@')
        email = f"{name_parts[0]}{counter}@{name_parts[1]}"
        counter += 1

    # Generate student_id for doctors if not provided properly
    if user.role == "doctor":
        # Use a numeric ID for doctors based on timestamp
        import time
        doctor_id = str(int(time.time()))[-7:]  # Last 7 digits of timestamp
        student_id = f"D{doctor_id}"
    else:
        student_id = user.student_id

    # Create user
    db_user = models.User(
        username=user.username,
        password_hash=hash_password(user.password),
        full_name=user.full_name,
        email=email,
        student_id=student_id,
        institution="Al Akhawayn University",
        department=user.department if user.role == "student" else None,
        major=user.major if user.role == "student" else user.specialization,
        academic_year="2025/2026",
        phone=user.phone,
        date_of_birth=datetime.strptime(user.date_of_birth, "%Y-%m-%d").date()
        if user.date_of_birth else None,
        gender=user.gender,
        year_level=user.year_level if user.role == "student" else None,
        role=user.role,
    )

    db.add(db_user)
    db.flush()  # Get the user ID

    # If doctor, create doctor entry linked to user
    if user.role == "doctor":
        # Generate avatar initials
        name_parts = user.full_name.split()
        avatar = ''.join([n[0].upper() for n in name_parts[:2]]) if len(name_parts) >= 2 else user.full_name[:2].upper()
        
        doctor = models.Doctor(
            user_id=db_user.id,
            name=user.full_name,
            license_number=user.license_number,
            specialty=user.specialization,
            email=email,
            phone=user.phone,
            avatar=avatar,
            rating=0.0,
            reviews_count=0,
            is_available=True
        )
        db.add(doctor)

    db.commit()
    db.refresh(db_user)

    token = create_access_token({"sub": db_user.username})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": db_user.username,
            "full_name": db_user.full_name,
            "email": db_user.email,
            "student_id": db_user.student_id,
            "role": db_user.role,
            "department": db_user.department,
            "major": db_user.major
        }
    }


@app.post("/auth/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(
        models.User.username == user.username
    ).first()

    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(401, "Invalid credentials")

    token = create_access_token({"sub": db_user.username})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": db_user.username,
            "full_name": db_user.full_name,
            "email": db_user.email,
            "student_id": db_user.student_id,
            "role": db_user.role,
            "department": db_user.department,
            "major": db_user.major
        }
    }


# ---------------------------------------------------------
# PROFILE
# ---------------------------------------------------------
@app.get("/profile")
def get_profile(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emergency = db.query(models.EmergencyContact).filter(
        models.EmergencyContact.user_id == current_user.id
    ).first()

    response = {
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "student_id": current_user.student_id,
        "department": current_user.department,
        "major": current_user.major,
        "phone": current_user.phone,
        "date_of_birth": current_user.date_of_birth.isoformat()
        if current_user.date_of_birth else None,
        "gender": current_user.gender,
        "year_level": current_user.year_level,
        "role": current_user.role,
        "emergency_contact": {
            "name": emergency.name,
            "relationship": emergency.relationship,
            "phone": emergency.phone,
            "email": emergency.email
        } if emergency else None,
    }
    
    # If doctor, add doctor-specific info
    if current_user.role == "doctor":
        doctor = db.query(models.Doctor).filter(
            models.Doctor.user_id == current_user.id
        ).first()
        if doctor:
            response["license_number"] = doctor.license_number
            response["specialty"] = doctor.specialty
            response["rating"] = doctor.rating
            response["reviews_count"] = doctor.reviews_count
    
    return response


@app.put("/profile/update")
def update_profile(
    updates: UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if updates.full_name:
        current_user.full_name = updates.full_name
        current_user.email = generate_aui_email(updates.full_name)
        
        # Update doctor name if applicable
        if current_user.role == "doctor":
            doctor = db.query(models.Doctor).filter(
                models.Doctor.user_id == current_user.id
            ).first()
            if doctor:
                doctor.name = updates.full_name
                doctor.email = current_user.email

    if updates.phone:
        current_user.phone = updates.phone

    if updates.date_of_birth:
        current_user.date_of_birth = datetime.strptime(
            updates.date_of_birth, "%Y-%m-%d"
        ).date()

    if updates.gender:
        current_user.gender = updates.gender

    if updates.department:
        if updates.department not in ["SSE", "SBA", "SSAH"]:
            raise HTTPException(400, "Invalid department")
        current_user.department = updates.department

    if updates.major:
        current_user.major = updates.major

    if updates.year_level:
        current_user.year_level = updates.year_level

    db.commit()
    db.refresh(current_user)

    return {
        "message": "Profile updated",
        "email": current_user.email
    }


@app.put("/profile/emergency-contact")
def update_emergency_contact(
    contact: EmergencyContactUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(models.EmergencyContact).filter(
        models.EmergencyContact.user_id == current_user.id
    ).first()

    if existing:
        existing.name = contact.name
        existing.relationship = contact.relationship
        existing.phone = contact.phone
        existing.email = contact.email
    else:
        new_contact = models.EmergencyContact(
            user_id=current_user.id,
            name=contact.name,
            relationship=contact.relationship,
            phone=contact.phone,
            email=contact.email,
        )
        db.add(new_contact)

    db.commit()
    return {"message": "Emergency contact updated"}


# ---------------------------------------------------------
# MEDICAL RECORDS
# ---------------------------------------------------------
@app.get("/medical-records")
def get_medical_records(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    records = db.query(models.MedicalRecord).filter(
        models.MedicalRecord.user_id == current_user.id,
        models.MedicalRecord.is_active == True
    ).all()

    return {
        "allergies": [
            {"id": r.id, "name": r.name, "severity": r.severity, "description": r.description}
            for r in records if r.type == "allergy"
        ],
        "medications": [
            {"id": r.id, "name": r.name, "description": r.description}
            for r in records if r.type == "medication"
        ],
        "conditions": [
            {"id": r.id, "name": r.name, "severity": r.severity, "description": r.description}
            for r in records if r.type == "condition"
        ],
    }


@app.post("/medical-records/entry")
def add_medical_entry(
    entry: MedicalEntryCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if entry.type not in ["allergy", "medication", "condition"]:
        raise HTTPException(400, "Invalid entry type")

    db_entry = models.MedicalRecord(
        user_id=current_user.id,
        type=entry.type,
        name=entry.name,
        description=entry.description,
        severity=entry.severity,
        diagnosed_date=datetime.strptime(entry.diagnosed_date, "%Y-%m-%d").date()
        if entry.diagnosed_date else None,
    )

    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)

    return {"message": "Entry added", "id": db_entry.id}


@app.put("/medical-records/{entry_id}")
def update_medical_entry(
    entry_id: int,
    updates: MedicalEntryUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = db.query(models.MedicalRecord).filter(
        models.MedicalRecord.id == entry_id,
        models.MedicalRecord.user_id == current_user.id,
    ).first()

    if not entry:
        raise HTTPException(404, "Entry not found")

    if updates.name:
        entry.name = updates.name
    if updates.description:
        entry.description = updates.description
    if updates.severity:
        entry.severity = updates.severity
    if updates.is_active is not None:
        entry.is_active = updates.is_active

    db.commit()
    return {"message": "Entry updated"}


@app.delete("/medical-records/{entry_id}")
def delete_medical_entry(
    entry_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = db.query(models.MedicalRecord).filter(
        models.MedicalRecord.id == entry_id,
        models.MedicalRecord.user_id == current_user.id,
    ).first()

    if not entry:
        raise HTTPException(404, "Entry not found")

    entry.is_active = False
    db.commit()
    return {"message": "Entry deleted"}


# ---------------------------------------------------------
# VISITS
# ---------------------------------------------------------
@app.get("/visits/all")
def get_all_visits(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    visits = db.query(models.Visit).filter(
        models.Visit.user_id == current_user.id
    ).order_by(models.Visit.visit_date.desc()).all()
    
    total = len(visits)
    upcoming = len([v for v in visits if v.status == "upcoming"])
    completed = len([v for v in visits if v.status == "completed"])
    cancelled = len([v for v in visits if v.status == "cancelled"])
    
    return {
        "statistics": {
            "total": total,
            "upcoming": upcoming,
            "completed": completed,
            "cancelled": cancelled
        },
        "visits": [
            {
                "id": v.id,
                "date": v.visit_date.isoformat(),
                "time_start": v.time_start,
                "time_end": v.time_end,
                "doctor_name": v.doctor.name if v.doctor else "Unknown",
                "diagnosis": v.diagnosis,
                "type": v.type,
                "location": v.location,
                "notes": v.notes,
                "status": v.status
            }
            for v in visits
        ]
    }


# ---------------------------------------------------------
# DOCTORS
# ---------------------------------------------------------
@app.get("/doctors")
def get_doctors(db: Session = Depends(get_db)):
    doctors = db.query(models.Doctor).filter(
        models.Doctor.is_available == True
    ).all()

    return [
        {
            "id": d.id,
            "name": d.name,
            "specialty": d.specialty,
            "rating": d.rating,
            "reviews": d.reviews_count,
            "avatar": d.avatar,
            "email": d.email,
            "phone": d.phone
        }
        for d in doctors
    ]


# ---------------------------------------------------------
# EMERGENCY
# ---------------------------------------------------------
@app.post("/emergency")
def create_emergency_request(
    request: EmergencyRequestCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emergency = models.EmergencyRequest(
        user_id=current_user.id,
        type=request.type,
        description=request.description,
        location=request.location,
        latitude=request.latitude,
        longitude=request.longitude,
        status="active",
        priority="high",
    )

    db.add(emergency)
    db.commit()

    return {"message": "Emergency request created", "id": emergency.id}


# ---------------------------------------------------------
# APPOINTMENTS
# ---------------------------------------------------------
@app.get("/appointments")
def get_appointments(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all appointments for current user"""
    appointments = db.query(models.Appointment).filter(
        models.Appointment.user_id == current_user.id
    ).order_by(models.Appointment.appointment_date.desc()).all()
    
    return [
        {
            "id": a.id,
            "doctor_id": a.doctor_id,
            "doctor_name": a.doctor.name if a.doctor else "Unknown",
            "doctor_specialty": a.doctor.specialty if a.doctor else "",
            "date": a.appointment_date.isoformat() if a.appointment_date else None,
            "time": a.appointment_time,
            "type": a.type,
            "location": a.location,
            "status": a.status,
            "notes": a.notes,
            "can_reschedule": a.can_reschedule
        }
        for a in appointments
    ]


@app.post("/appointments")
def create_appointment(
    appointment: AppointmentCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new appointment"""
    # Verify doctor exists
    doctor = db.query(models.Doctor).filter(
        models.Doctor.id == appointment.doctor_id
    ).first()
    
    if not doctor:
        raise HTTPException(404, "Doctor not found")
    
    # Parse date
    try:
        appt_date = datetime.strptime(appointment.appointment_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD")
    
    # Check if slot is available (basic check)
    existing = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == appointment.doctor_id,
        models.Appointment.appointment_date == appt_date,
        models.Appointment.appointment_time == appointment.appointment_time,
        models.Appointment.status != "cancelled"
    ).first()
    
    if existing:
        raise HTTPException(400, "This time slot is already booked")
    
    # Create appointment
    db_appointment = models.Appointment(
        user_id=current_user.id,
        doctor_id=appointment.doctor_id,
        appointment_date=appt_date,
        appointment_time=appointment.appointment_time,
        type=appointment.type,
        location=f"Campus Health Center, Room {doctor.id}01",
        notes=appointment.notes,
        status="upcoming",
        can_reschedule=True
    )
    
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    
    return {
        "message": "Appointment created successfully",
        "id": db_appointment.id,
        "date": db_appointment.appointment_date.isoformat(),
        "time": db_appointment.appointment_time,
        "doctor": doctor.name
    }


@app.put("/appointments/{appointment_id}")
def update_appointment(
    appointment_id: int,
    updates: AppointmentUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reschedule an appointment"""
    appointment = db.query(models.Appointment).filter(
        models.Appointment.id == appointment_id,
        models.Appointment.user_id == current_user.id
    ).first()
    
    if not appointment:
        raise HTTPException(404, "Appointment not found")
    
    if appointment.status == "cancelled":
        raise HTTPException(400, "Cannot modify a cancelled appointment")
    
    # Check 12-hour rule
    if appointment.appointment_date:
        hours_until = (appointment.appointment_date - datetime.now()).total_seconds() / 3600
        if hours_until < 12:
            raise HTTPException(400, "Cannot reschedule within 12 hours of appointment")
    
    # Update fields
    if updates.appointment_date:
        appointment.appointment_date = datetime.strptime(updates.appointment_date, "%Y-%m-%d")
    if updates.appointment_time:
        appointment.appointment_time = updates.appointment_time
    if updates.type:
        appointment.type = updates.type
    if updates.notes:
        appointment.notes = updates.notes
    
    db.commit()
    
    return {"message": "Appointment updated successfully"}


@app.delete("/appointments/{appointment_id}")
def cancel_appointment(
    appointment_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel an appointment"""
    appointment = db.query(models.Appointment).filter(
        models.Appointment.id == appointment_id,
        models.Appointment.user_id == current_user.id
    ).first()
    
    if not appointment:
        raise HTTPException(404, "Appointment not found")
    
    appointment.status = "cancelled"
    appointment.can_reschedule = False
    db.commit()
    
    return {"message": "Appointment cancelled successfully"}


@app.get("/doctors/{doctor_id}/available-slots")
def get_available_slots(
    doctor_id: int,
    date: str,
    db: Session = Depends(get_db),
):
    """Get available time slots for a doctor on a specific date"""
    # Verify doctor exists
    doctor = db.query(models.Doctor).filter(
        models.Doctor.id == doctor_id,
        models.Doctor.is_available == True
    ).first()

    if not doctor:
        raise HTTPException(404, "Doctor not found or not available")

    # Parse the date
    try:
        appointment_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD")

    # Define all possible time slots (30-minute intervals)
    all_slots = [
        '09:00 AM', '09:30 AM', '10:00 AM', '10:30 AM',
        '11:00 AM', '11:30 AM', '12:00 PM', '12:30 PM',
        '02:00 PM', '02:30 PM', '03:00 PM', '03:30 PM',
        '04:00 PM', '04:30 PM', '05:00 PM'
    ]

    # Get all booked appointments for this doctor on this date (excluding cancelled)
    booked_appointments = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == doctor_id,
        models.Appointment.appointment_date == appointment_date,
        models.Appointment.status != "cancelled"
    ).all()

    # Get list of booked time slots
    booked_slots = [apt.appointment_time for apt in booked_appointments]

    # Filter out booked slots from available slots
    available_slots = [slot for slot in all_slots if slot not in booked_slots]

    return {
        "doctor_id": doctor_id,
        "doctor_name": doctor.name,
        "date": date,
        "available_slots": available_slots,
        "booked_slots": booked_slots
    }


# Add this to backend/main.py after the appointments endpoints

@app.get("/appointments/upcoming")
def get_upcoming_appointments(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get upcoming appointments (future appointments that are not cancelled)"""
    today = datetime.now().date()
    
    appointments = db.query(models.Appointment).filter(
        models.Appointment.user_id == current_user.id,
        models.Appointment.appointment_date >= today,
        models.Appointment.status != "cancelled"
    ).order_by(models.Appointment.appointment_date.asc()).all()
    
    result = []
    for a in appointments:
        # Calculate if can reschedule (12 hour rule)
        appointment_datetime = datetime.combine(a.appointment_date, datetime.min.time())
        hours_until = (appointment_datetime - datetime.now()).total_seconds() / 3600
        can_reschedule = hours_until > 12
        
        result.append({
            "id": a.id,
            "doctor_id": a.doctor_id,
            "doctor_name": a.doctor.name if a.doctor else "Unknown",
            "doctor_specialty": a.doctor.specialty if a.doctor else "",
            "date": a.appointment_date.isoformat() if a.appointment_date else None,
            "time": a.appointment_time,
            "type": a.type,
            "location": a.location,
            "status": a.status,
            "notes": a.notes,
            "can_reschedule": can_reschedule,
            "hours_until": hours_until
        })
    
    return result


@app.post("/appointments/{appointment_id}/complete")
def complete_appointment(
    appointment_id: int,
    diagnosis: str = None,
    notes: str = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mark an appointment as completed and create a visit record.
    This should be called by doctors or automatically after the appointment time.
    """
    appointment = db.query(models.Appointment).filter(
        models.Appointment.id == appointment_id
    ).first()
    
    if not appointment:
        raise HTTPException(404, "Appointment not found")
    
    # Update appointment status
    appointment.status = "completed"
    
    # Create a visit record from the completed appointment
    visit = models.Visit(
        user_id=appointment.user_id,
        doctor_id=appointment.doctor_id,
        visit_date=appointment.appointment_date,
        time_start=appointment.appointment_time,
        time_end=appointment.appointment_time,  # You can calculate end time
        diagnosis=diagnosis or "General Consultation",
        type=appointment.type,
        location=appointment.location,
        notes=notes or appointment.notes or "Appointment completed",
        status="completed"
    )
    
    db.add(visit)
    db.commit()
    db.refresh(visit)
    
    return {
        "message": "Appointment completed and added to visit history",
        "visit_id": visit.id,
        "appointment_id": appointment.id
    }


@app.get("/visits/recent")
def get_recent_visits(
    limit: int = 3,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get recent completed visits"""
    visits = db.query(models.Visit).filter(
        models.Visit.user_id == current_user.id,
        models.Visit.status == "completed"
    ).order_by(models.Visit.visit_date.desc()).limit(limit).all()
    
    return [
        {
            "id": v.id,
            "date": v.visit_date.isoformat(),
            "time_start": v.time_start,
            "time_end": v.time_end,
            "doctor_name": v.doctor.name if v.doctor else "Unknown",
            "diagnosis": v.diagnosis,
            "type": v.type,
            "location": v.location,
            "notes": v.notes,
            "status": v.status
        }
        for v in visits
    ]

# ---------------------------------------------------------
# PERMANENT DELETE MEDICAL RECORD
# ---------------------------------------------------------
@app.delete("/medical-records/{entry_id}/permanent")
def permanently_delete_medical_entry(
    entry_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Permanently delete a medical entry"""
    entry = db.query(models.MedicalRecord).filter(
        models.MedicalRecord.id == entry_id,
        models.MedicalRecord.user_id == current_user.id,
    ).first()

    if not entry:
        raise HTTPException(404, "Entry not found")

    db.delete(entry)
    db.commit()
    return {"message": "Entry permanently deleted"}


# ---------------------------------------------------------
# DOCTOR DASHBOARD ENDPOINTS
# ---------------------------------------------------------
@app.get("/doctor/patients")
def get_doctor_patients(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get patients for a doctor"""
    if current_user.role != "doctor":
        raise HTTPException(403, "Access denied. Doctors only.")
    
    # Get doctor record
    doctor = db.query(models.Doctor).filter(
        models.Doctor.user_id == current_user.id
    ).first()
    
    if not doctor:
        raise HTTPException(404, "Doctor profile not found")
    
    # Get today's appointments
    today = datetime.now().date()
    appointments = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == doctor.id,
        models.Appointment.appointment_date == today,
        models.Appointment.status == "upcoming"
    ).all()
    
    return [
        {
            "id": a.id,
            "patient_name": a.user.full_name if a.user else "Unknown",
            "patient_id": a.user.student_id if a.user else "N/A",
            "time": a.appointment_time,
            "type": a.type,
            "notes": a.notes
        }
        for a in appointments
    ]


@app.get("/doctor/schedule")
def get_doctor_schedule(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get doctor's schedule"""
    if current_user.role != "doctor":
        raise HTTPException(403, "Access denied. Doctors only.")
    
    doctor = db.query(models.Doctor).filter(
        models.Doctor.user_id == current_user.id
    ).first()
    
    if not doctor:
        raise HTTPException(404, "Doctor profile not found")
    
    # Get all upcoming appointments
    appointments = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == doctor.id,
        models.Appointment.status == "upcoming"
    ).order_by(models.Appointment.appointment_date).all()
    
    return {
        "doctor_name": doctor.name,
        "specialty": doctor.specialty,
        "appointments": [
            {
                "id": a.id,
                "patient_name": a.user.full_name if a.user else "Unknown",
                "date": a.appointment_date.isoformat() if a.appointment_date else None,
                "time": a.appointment_time,
                "type": a.type,
                "status": a.status
            }
            for a in appointments
        ]
    }


# ---------------------------------------------------------
# CHATBOT ENDPOINTS
# ---------------------------------------------------------
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    user_context: Optional[dict] = None


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str
    model: Optional[str] = None
    mode: Optional[str] = None


@app.post("/chat/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        from chatbot import ai_reply

        conversation_id = request.conversation_id or f"conv_{datetime.utcnow().timestamp()}"
        
        result = ai_reply(
            message=request.message,
            conversation_id=conversation_id,
            user_context=request.user_context,
        )

        return ChatResponse(
            reply=result.get("reply", "I'm having trouble responding."),
            conversation_id=result.get("conversation_id", conversation_id),
            model=result.get("model"),
            mode=result.get("mode"),
        )

    except Exception as e:
        print("Chatbot error:", e)
        return ChatResponse(
            reply="I'm having technical difficulties.",
            conversation_id=request.conversation_id or "error",
            mode="error",
        )


# ---------------------------------------------------------
# STARTUP EVENT - Initialize Database
# ---------------------------------------------------------
@app.on_event("startup")
def startup_event():
    """Initialize database on startup"""
    from database import init_db
    init_db()


# ---------------------------------------------------------
# RUN SERVER
# ---------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting CareConnect API Server...")
    print("📍 Server: http://127.0.0.1:8000")
    print("📚 Docs: http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)