# # main.py

# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from chatbot import EllaChatbot

# app = FastAPI()
# chatbot = EllaChatbot()

# class ChatRequest(BaseModel):
#     user_id: str
#     message: str

# @app.post("/chat")
# def chat(request: ChatRequest):
#     try:
#         response = chatbot.get_response(request.user_id, request.message)
#         return {"response": response}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
import db
from chatbot import EllaChatbot
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Chatbot API")
chatbot = EllaChatbot()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "pinecone": "connected",
            "openai": "connected",
            "mongodb": "connected"
        }
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Caroline Chatbot API is running!",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "users": "/users",
            "chat": "/chat"
        }
    }

# Pydantic models for request/response
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    age: int
    gender: str
    preferences: Optional[dict] = {"loves": [], "dislikes": [], "interests": []}

class Message(BaseModel):
    content: str
    is_user: bool = True
    emotion: Optional[str] = None

class ChatSession(BaseModel):
    user_id: str
    messages: List[Message]

# User endpoints
@app.post("/users/")
async def create_user(user: UserCreate):
    try:
        result = db.create_user(user.dict())
        return {"user_id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Chat endpoints
@app.post("/chat/{user_id}")
async def create_chat(user_id: str):
    try:
        result = db.create_chat_session(user_id)
        return {"chat_id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/chat/{chat_id}/message")
async def send_message(chat_id: str, message: Message):
    try:
        # Get chatbot response
        bot_response = chatbot.get_response(chat_id, message.content)
        
        # Store user message
        db.add_message(chat_id, message.dict())
        
        # Store bot response
        bot_message = Message(
            content=bot_response,
            is_user=False,
            emotion=chatbot.emotion_handler.detect_emotion(bot_response)
        )
        db.add_message(chat_id, bot_message.dict())
        
        return {"response": bot_response}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/chat/{chat_id}/history")
async def get_chat_history(chat_id: str, limit: int = 50):
    history = db.get_chat_history(chat_id, limit)
    if not history:
        raise HTTPException(status_code=404, detail="Chat history not found")
    return history
