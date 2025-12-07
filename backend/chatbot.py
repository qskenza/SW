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
        #model = genai.GenerativeModel('gemini-1.5-flash')
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        AI_AVAILABLE = True
        print("✅ Google Gemini AI initialized successfully")
except Exception as e:
    print(f"⚠️ Google AI initialization failed: {e}")
    AI_AVAILABLE = False
    model = None

# Store conversations in memory
conversations = {}

SYSTEM_PROMPT = """You are a helpful AI assistant for a university health center named CareConnect.

Your role:
- Provide safe, simple, evidence-based health guidance in English
- Answer questions about appointments, medical records, and health center services
- Be concise, professional, and compassionate
- Always respond in English

Important limitations:
- You are NOT a doctor and cannot provide medical diagnoses
- Always encourage users to seek professional medical help for serious symptoms
- Never prescribe medications
- In emergencies, direct users to call emergency services (911) or use the emergency request feature

Health Center Services:
- Appointment booking with doctors
- Medical records management
- Emergency request system
- General health consultations
- Prescription refills

Be helpful, empathetic, and encourage proper medical care when needed. Keep responses under 200 words."""

def get_conversation(conversation_id: str) -> List[Dict]:
    """Get or create conversation history"""
    if conversation_id not in conversations:
        conversations[conversation_id] = []
    return conversations[conversation_id]

def ai_reply(message: str, conversation_id: str = "default", user_context: Dict = None) -> Dict:
    """
    Generate AI reply with conversation context using Google Gemini
    """
    if not AI_AVAILABLE or model is None:
        print(f"⚠️ Using fallback mode for message: {message}")
        
        # Fallback responses in English
        fallback_responses = {
            "hello": "Hello! I'm the CareConnect health assistant. How can I help you today?",
            "hi": "Hi! I'm here to assist you with health-related questions. What can I help you with?",
            "appointment": "To book an appointment, please use the 'Appointments' section on our website or contact the health center directly.",
            "book": "To schedule an appointment, please visit the Appointments section on our website.",
            "emergency": "⚠️ If this is a medical emergency, please use the red emergency button or call 911 immediately!",
            "urgent": "⚠️ For urgent medical situations, please call 911 or use our emergency request feature right away!",
            "headache": "For a headache, I recommend resting in a quiet, dark room. Stay hydrated and consider over-the-counter pain relief. If the pain persists or worsens, please consult a doctor.",
            "pain": "For persistent pain, I recommend scheduling an appointment with a healthcare provider. You can book through our appointment system.",
            "help": "I can help you with: booking appointments, accessing medical records, answering general health questions, and emergency assistance. How can I assist you?",
            "records": "To access your medical records, please use the 'Medical Records' section in your dashboard.",
            "doctor": "Our doctors are available for consultations. You can schedule an appointment through the Appointments section.",
            "default": "I'm currently in limited mode. I can provide general information. For appointments or medical records, please use the dedicated sections on our website. For urgent medical assistance, contact the health center directly."
        }
        
        message_lower = message.lower()
        reply = fallback_responses["default"]
        
        # Match keywords to responses
        for keyword, response in fallback_responses.items():
            if keyword in message_lower:
                reply = response
                break
        
        return {
            "reply": reply,
            "conversation_id": conversation_id,
            "mode": "fallback",
            "note": "⚠️ Limited mode - Google AI key not configured. Add your Google AI key to .env to activate full AI features."
        }
    
    try:
        # Get conversation history
        conversation = get_conversation(conversation_id)
        
        # Build full prompt with context
        full_prompt = SYSTEM_PROMPT + "\n\n"
        
        # Add conversation history
        if conversation:
            full_prompt += "Conversation history:\n"
            for msg in conversation[-10:]:  # Last 10 messages
                role = "User" if msg["role"] == "user" else "Assistant"
                full_prompt += f"{role}: {msg['content']}\n"
            full_prompt += "\n"
        
        # Add user context if provided
        if user_context:
            full_prompt += f"User info: Name: {user_context.get('name', 'Unknown')}, Student ID: {user_context.get('student_id', 'N/A')}\n\n"
        
        # Add current message
        full_prompt += f"User: {message}\n\nAssistant:"
        
        # Call Google Gemini API
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=300,
                temperature=0.7,
            )
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
            "model": "gemini-2.5-flash-lite"
           
        }
    
    except Exception as e:
        print(f"❌ Gemini API error: {e}")
        return {
            "reply": f"Sorry, an error occurred: {str(e)}. Please try again or contact support.",
            "conversation_id": conversation_id,
            "error": str(e)
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
        "severe pain", "bleeding heavily", "unconscious", "suicide",
        "severe bleeding", "can't breathe"
    ]
    
    message_lower = message.lower()
    is_urgent = any(keyword in message_lower for keyword in emergency_keywords)
    
    return {
        "is_urgent": is_urgent,
        "urgency_level": "high" if is_urgent else "normal",
        "recommendation": "Please use the emergency request feature or call emergency services immediately." if is_urgent else None
    }