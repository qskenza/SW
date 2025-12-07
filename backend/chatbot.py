from dotenv import load_dotenv
import os
from typing import List, Dict
import json

# Fix for Python 3.13 compatibility
import collections.abc
collections.MutableSet = collections.abc.MutableSet

load_dotenv()

# Try to import Google Generative AI
try:
    import google.generativeai as genai
    
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        print("⚠️ GOOGLE_API_KEY not found in .env file")
        AI_AVAILABLE = False
        model = None
    else:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        AI_AVAILABLE = True
        print("✅ Google Gemini AI initialized successfully")
except Exception as e:
    print(f"⚠️ Google AI initialization failed: {e}")
    AI_AVAILABLE = False
    model = None

# Store conversations in memory
conversations = {}

SYSTEM_PROMPT = """You are a helpful AI assistant for Al Akhawayn University's health center named CareConnect.

Your role is to GUIDE and INFORM students and doctors - NOT to perform actions for them.

WHAT YOU DO:
✅ Answer questions about health center services and features
✅ Explain HOW to use the system (appointments, medical records, emergency features)
✅ Provide general health information and wellness guidance
✅ Direct users to the correct page/feature for their specific needs
✅ Explain what each feature does and how it helps them
✅ Be compassionate, supportive, and encouraging

WHAT YOU DON'T DO:
❌ Add medical entries - instead, direct them to "Add Medical Entry" page
❌ Edit profiles - instead, direct them to "Edit Profile" page
❌ Book appointments - instead, direct them to "Appointments" page
❌ Make emergency calls - instead, direct them to "Emergency Request" page
❌ Access or modify their data directly
❌ Provide medical diagnoses or prescribe medications
❌ Perform any actions in the system on their behalf

CRITICAL: You are a GUIDE, not an EXECUTOR. You explain how things work and where to find features.

HOW TO RESPOND TO ACTION REQUESTS:

Example 1 - Adding Medical Entry:
User: "Can you add my peanut allergy?"
You: "I can't add entries directly, but I'll guide you through it! Here's how:

1. Go to your Dashboard
2. Click the 'Add Medical Entry' button
3. Select 'Allergy' as the type
4. Enter 'Peanuts' as the name
5. Choose the severity level (mild/moderate/severe)
6. Click 'Save'

Your entry will be saved to the database immediately. Would you like me to explain any of these steps in more detail?"

Example 2 - Updating Profile:
User: "Update my phone number to +212 123-4567"
You: "I'll show you how to update it yourself! Here's the process:

1. Go to 'Student Profile' (top navigation)
2. Click the 'Edit Profile' button
3. Find the 'Phone Number' field
4. Enter your new number: +212 123-4567
5. Click 'Save Changes'

Your profile updates instantly in the database. Note: If you change your name, your AUI email will automatically regenerate to match!"

Example 3 - Emergency:
User: "I need emergency help!"
You: "⚠️ For immediate emergencies:

• Click the red 'Emergency Request' button in the navigation
• Or call Emergency Services directly: 2222
• If life-threatening: Call Campus Security: 0535-86-0103

The Emergency Request page lets you:
- Call emergency services with one click
- Share your GPS location automatically
- Contact campus doctors directly

Is this a medical emergency? If yes, please use those options NOW!"

IMPORTANT MEDICAL LIMITATIONS:
- You are NOT a doctor and cannot diagnose conditions
- You cannot prescribe medications or treatments
- Always encourage professional medical evaluation for symptoms
- Never suggest delaying emergency care
- In emergencies, ALWAYS direct to Emergency Request page or emergency numbers

AUI-SPECIFIC INFORMATION:
- Institution: Al Akhawayn University (Ifrane, Morocco)
- Departments: 
  * SSE - School of Science and Engineering
  * SBA - School of Business Administration
  * SSAH - School of Social Sciences and Humanities
- Email format: (first letter of first name).(last name)@aui.ma
  Example: Alexandra Miller → a.miller@aui.ma
- Emergency Services: 2222
- Campus Security: 0535-86-0103
- Health Center: 0535-86-0104
- Emergency Hotline: 0535 86 2222 (24/7)
- Academic Year: 2025/2026
- Student ID Format: Numbers only (e.g., 2023001)

DATABASE FEATURES (Explain to users):
- All changes save to database in real-time
- Profile updates persist across sessions
- Medical records can be added, edited, or deleted
- Emergency requests are logged with timestamps
- Visit history is permanently stored
- Email auto-regenerates when name changes

SYSTEM FEATURES YOU CAN EXPLAIN:
1. Medical Dashboard - View health info, upcoming appointments, medical records
2. Appointments - Book with available doctors, reschedule (if >12 hours away)
3. Student Profile - View personal info, academic details, emergency contact
4. Edit Profile - Update all profile fields, auto-generates AUI email
5. Add Medical Entry - Add allergies, medications, or conditions
6. Visit History - View past visits with doctors, download reports
7. Emergency Request - Call emergency services, share location, view procedures

Be helpful, clear, empathetic, and concise. Keep responses under 200 words unless explaining a complex process. Always respond in English. Use formatting (bullets, numbers) to make instructions clear.

Remember: You GUIDE users to features - you DON'T perform actions for them!"""

def detect_action_intent(message: str) -> Dict:
    """Detect if user is asking chatbot to perform an action"""
    
    action_patterns = {
        "add_medical": [
            "add my", "add an", "add a", "create a", "create my",
            "new allergy", "new medication", "new condition",
            "add allergy", "add medication", "record my"
        ],
        "edit_profile": [
            "change my", "update my", "edit my", "modify my",
            "change the", "update the", "edit the"
        ],
        "book_appointment": [
            "book", "schedule", "make an appointment", "set up appointment",
            "see a doctor", "appointment with"
        ],
        "delete_entry": [
            "delete my", "remove my", "delete the", "remove the"
        ],
        "emergency": [
            "call emergency", "emergency now", "help me now",
            "i need help", "urgent help", "emergency call"
        ]
    }
    
    message_lower = message.lower()
    
    for action, keywords in action_patterns.items():
        if any(keyword in message_lower for keyword in keywords):
            return {
                "is_action_request": True,
                "action_type": action,
                "needs_guidance": True
            }
    
    return {"is_action_request": False}

def get_conversation(conversation_id: str) -> List[Dict]:
    """Get or create conversation history"""
    if conversation_id not in conversations:
        conversations[conversation_id] = []
    return conversations[conversation_id]

def get_guidance_reminder(action_type: str) -> str:
    """Get specific reminder based on action type"""
    reminders = {
        "add_medical": "\n⚠️ REMINDER: User wants to add a medical entry. Guide them to 'Add Medical Entry' page - DO NOT say you'll add it yourself!",
        "edit_profile": "\n⚠️ REMINDER: User wants to edit their profile. Guide them to 'Edit Profile' page - DO NOT say you'll update it yourself!",
        "book_appointment": "\n⚠️ REMINDER: User wants to book an appointment. Guide them to 'Appointments' page - DO NOT say you'll book it yourself!",
        "delete_entry": "\n⚠️ REMINDER: User wants to delete an entry. Explain how to do it from Dashboard - DO NOT say you'll delete it yourself!",
        "emergency": "\n⚠️ CRITICAL: This is an emergency. Direct them to Emergency Request page or emergency numbers IMMEDIATELY!"
    }
    return reminders.get(action_type, "")

def ai_reply(message: str, conversation_id: str = "default", user_context: Dict = None) -> Dict:
    """
    Generate AI reply with conversation context using Google Gemini
    """
    if not AI_AVAILABLE or model is None:
        print(f"⚠️ Using fallback mode for message: {message}")
        
        # Enhanced fallback responses
        fallback_responses = {
            "hello": "Hello! I'm the CareConnect assistant for Al Akhawayn University. I can help you understand how to use our health center features. How can I guide you today?",
            "hi": "Hi! I'm here to guide you through CareConnect's features. What would you like to know about?",
            "appointment": "To book an appointment:\n1. Click 'Appointments' in the navigation\n2. Select a doctor\n3. Choose date and time\n4. Click 'Book Appointment'\n\nThe system will save it to the database!",
            "book": "I can't book appointments for you, but I'll guide you! Go to the 'Appointments' section and follow the booking steps. Need help understanding any part?",
            "emergency": "⚠️ FOR EMERGENCIES:\n• Click 'Emergency Request' in navigation\n• Or call 2222 immediately\n• Campus Security: 0535-86-0103\n\nIs this urgent?",
            "urgent": "⚠️ If this is a medical emergency:\n1. Use the Emergency Request page NOW\n2. Or call 2222\n3. For life-threatening: Call campus security\n\nDon't delay - get help immediately!",
            "add": "I can't add entries for you, but here's how:\n1. Go to Dashboard\n2. Click 'Add Medical Entry'\n3. Fill in the details\n4. Click Save\n\nWhat type of entry do you need to add?",
            "profile": "To edit your profile:\n1. Go to 'Student Profile'\n2. Click 'Edit Profile'\n3. Update the fields\n4. Click 'Save Changes'\n\nYour AUI email will auto-update if you change your name!",
            "help": "I can guide you with:\n• How to book appointments\n• How to add medical records\n• How to update your profile\n• How to use emergency features\n• General health information\n\nWhat would you like to know about?",
            "records": "To access medical records:\n1. Go to 'Medical Dashboard'\n2. Scroll to 'Medical Information'\n3. View or click 'Add Medical Entry' to add new ones\n\nAll changes save to the database instantly!",
            "doctor": "To see a doctor:\n1. Go to 'Appointments'\n2. Browse available doctors\n3. Select one and choose time\n4. Book the appointment\n\nWould you like to know about our doctors?",
            "email": "AUI email format: (first letter).(lastname)@aui.ma\n\nExample: Alexandra Miller → a.miller@aui.ma\n\nYour email auto-updates when you change your name in Edit Profile!",
            "default": "I'm here to guide you through CareConnect! I can explain:\n• How to use appointments\n• How to manage medical records\n• How to update your profile\n• Emergency procedures\n\nWhat would you like to know?"
        }
        
        message_lower = message.lower()
        reply = fallback_responses["default"]
        
        # Match keywords to responses
        for keyword, response in fallback_responses.items():
            if keyword in message_lower:
                reply = response
                break
        
        # Check for action intent even in fallback
        action_check = detect_action_intent(message)
        if action_check["is_action_request"]:
            reply += "\n\nNote: I can guide you through the process, but I can't perform actions for you. I'll show you exactly how to do it yourself!"
        
        return {
            "reply": reply,
            "conversation_id": conversation_id,
            "mode": "fallback",
            "note": "⚠️ Limited mode - Add GOOGLE_API_KEY to .env for full AI features."
        }
    
    try:
        # Check for action intent
        action_check = detect_action_intent(message)
        
        # Get conversation history
        conversation = get_conversation(conversation_id)
        
        # Build full prompt with context
        full_prompt = SYSTEM_PROMPT
        
        # Add action reminder if needed
        if action_check["is_action_request"]:
            full_prompt += get_guidance_reminder(action_check["action_type"])
        
        full_prompt += "\n\n"
        
        # Add conversation history
        if conversation:
            full_prompt += "Previous conversation:\n"
            for msg in conversation[-8:]:  # Last 8 messages for context
                role = "User" if msg["role"] == "user" else "Assistant"
                full_prompt += f"{role}: {msg['content']}\n"
            full_prompt += "\n"
        
        # Add user context if provided
        if user_context:
            full_prompt += f"Current user: {user_context.get('name', 'Unknown')} (ID: {user_context.get('student_id', 'N/A')})\n"
            if 'department' in user_context:
                full_prompt += f"Department: {user_context.get('department')} - {user_context.get('major', 'N/A')}\n"
            full_prompt += "\n"
        
        # Add current message
        full_prompt += f"User's message: {message}\n\nYour response (remember - GUIDE, don't act!):"
        
        # Call Google Gemini API
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=400,
                temperature=0.7,
            ),
            safety_settings=[
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
        )
        
        # Extract reply
        reply = response.text
        
        # Add messages to conversation history
        conversation.append({"role": "user", "content": message})
        conversation.append({"role": "assistant", "content": reply})
        
        # Keep only last 20 messages to manage memory
        if len(conversation) > 20:
            conversations[conversation_id] = conversation[-20:]
        
        return {
            "reply": reply,
            "conversation_id": conversation_id,
            "model": "gemini-2.0-flash-exp",
            "action_detected": action_check["is_action_request"],
            "action_type": action_check.get("action_type") if action_check["is_action_request"] else None
        }
    
    except Exception as e:
        print(f"❌ Gemini API error: {e}")
        
        # Fallback error response
        error_reply = "I apologize, but I'm having trouble connecting right now. "
        
        # Still try to help based on keywords
        message_lower = message.lower()
        if "emergency" in message_lower or "urgent" in message_lower:
            error_reply += "⚠️ If this is an emergency, please:\n• Use Emergency Request page\n• Call 2222\n• Or call Campus Security: 0535-86-0103"
        elif "appointment" in message_lower:
            error_reply += "For appointments, go to the 'Appointments' page in the navigation."
        elif "profile" in message_lower:
            error_reply += "To edit your profile, go to 'Student Profile' → 'Edit Profile'."
        else:
            error_reply += "Please try rephrasing your question, or contact the health center directly."
        
        return {
            "reply": error_reply,
            "conversation_id": conversation_id,
            "error": str(e),
            "mode": "error_fallback"
        }

def clear_conversation(conversation_id: str):
    """Clear conversation history"""
    if conversation_id in conversations:
        del conversations[conversation_id]
        return True
    return False

def analyze_urgency(message: str) -> Dict:
    """Analyze if message indicates an emergency"""
    emergency_keywords = [
        "emergency", "urgent", "chest pain", "difficulty breathing",
        "can't breathe", "severe pain", "bleeding heavily", 
        "unconscious", "suicide", "severe bleeding", "heart attack",
        "stroke", "choking", "overdose", "severe injury"
    ]
    
    message_lower = message.lower()
    is_urgent = any(keyword in message_lower for keyword in emergency_keywords)
    
    urgency_level = "high" if is_urgent else "normal"
    
    recommendation = None
    if is_urgent:
        recommendation = "⚠️ EMERGENCY DETECTED!\n\nPlease:\n1. Use Emergency Request page immediately\n2. Or call 2222\n3. Campus Security: 0535-86-0103\n\nDo not delay - get help NOW!"
    
    return {
        "is_urgent": is_urgent,
        "urgency_level": urgency_level,
        "recommendation": recommendation,
        "detected_keywords": [kw for kw in emergency_keywords if kw in message_lower]
    }

def get_quick_help(topic: str) -> str:
    """Get quick help for common topics"""
    help_topics = {
        "appointments": """📅 BOOKING APPOINTMENTS:
1. Click 'Appointments' in navigation
2. Browse available doctors
3. Select doctor and time slot
4. Click 'Book Appointment'
5. Confirm booking

✅ Saves to database immediately
⏰ Can reschedule if >12 hours away""",

        "medical_records": """📋 MANAGING MEDICAL RECORDS:
1. Go to 'Medical Dashboard'
2. View existing records in 'Medical Information' section
3. Click 'Add Medical Entry' to add new
4. Select type: Allergy, Medication, or Condition
5. Fill details and save

✅ All changes saved to database
🗑️ Can delete entries anytime""",

        "profile": """👤 EDITING PROFILE:
1. Go to 'Student Profile'
2. Click 'Edit Profile' button
3. Update any field (name, phone, department, etc.)
4. Click 'Save Changes'

✨ Special features:
• Email auto-updates if you change name
• Format: (first letter).(lastname)@aui.ma
• Emergency contact also editable""",

        "emergency": """🚨 EMERGENCY PROCEDURES:
For immediate help:
1. Click 'Emergency Request' in navigation
2. Or call 2222 directly
3. Campus Security: 0535-86-0103
4. 24/7 Hotline: 0535 86 2222

Features:
• One-click emergency calling
• GPS location sharing
• Direct contact with campus doctors""",

        "email": """📧 AUI EMAIL SYSTEM:
Format: (first letter).(last name)@aui.ma

Examples:
• Alexandra Miller → a.miller@aui.ma
• John Smith → j.smith@aui.ma

Auto-generation:
• Email updates when you change your name
• Go to Edit Profile → Change name → Save
• New email generated automatically!"""
    }
    
    return help_topics.get(topic.lower(), "Topic not found. Ask me about: appointments, medical_records, profile, emergency, or email")

# Optional: Rate limiting for safety
conversation_counts = {}

def check_rate_limit(conversation_id: str, limit: int = 50) -> bool:
    """Check if conversation has exceeded rate limit"""
    if conversation_id not in conversation_counts:
        conversation_counts[conversation_id] = 0
    
    conversation_counts[conversation_id] += 1
    
    if conversation_counts[conversation_id] > limit:
        return False
    
    return True