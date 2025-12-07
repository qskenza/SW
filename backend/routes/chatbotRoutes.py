from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid
from chatbot import ai_reply, clear_conversation, get_health_advice, analyze_urgency

router = APIRouter(prefix="/chat", tags=["Chatbot"])

class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    user_context: Optional[dict] = None

class SymptomCheck(BaseModel):
    symptom: str

class ConversationClear(BaseModel):
    conversation_id: str

@router.post("/")
def chat(data: ChatMessage):
    """
    Main chat endpoint with conversation context
    """
    # Generate conversation ID if not provided
    if not data.conversation_id:
        data.conversation_id = str(uuid.uuid4())
    
    # Analyze urgency
    urgency = analyze_urgency(data.message)
    
    # Get AI reply
    response = ai_reply(
        message=data.message,
        conversation_id=data.conversation_id,
        user_context=data.user_context
    )
    
    # Add urgency info if needed
    if urgency["is_urgent"]:
        response["urgency_alert"] = urgency
    
    return response

@router.post("/symptom-check")
def symptom_check(data: SymptomCheck):
    """
    Quick symptom checker without conversation history
    """
    advice = get_health_advice(data.symptom)
    urgency = analyze_urgency(data.symptom)
    
    return {
        "symptom": data.symptom,
        "advice": advice,
        "urgency": urgency
    }

@router.delete("/conversation")
def clear_chat(data: ConversationClear):
    """
    Clear conversation history
    """
    success = clear_conversation(data.conversation_id)
    if success:
        return {"message": "Conversation cleared successfully"}
    return {"message": "Conversation not found or already cleared"}

@router.get("/health")
def chatbot_health():
    """
    Check if chatbot service is operational
    """
    return {
        "status": "operational",
        "service": "CareConnect Health Assistant",
        "features": [
            "Multi-language support (English, French, Arabic)",
            "Conversation memory",
            "Urgency detection",
            "Health guidance"
        ]
    }