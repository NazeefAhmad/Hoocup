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
import traceback
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Chatbot API")
chatbot = None  # Will be initialized in startup event

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Startup event
@app.on_event("startup")
async def startup_event():
    try:
        # Initialize database
        await db.startup_db()
        # Initialize chatbot
        global chatbot
        chatbot = EllaChatbot()
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise

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

# Model for Flutter app requests
class ChatRequest(BaseModel):
    user_id: str
    message: str

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
            "chat": {
                "create_session": "/chat/{user_id}",
                "send_message": "/chat/{chat_id}/message",
                "get_history": "/chat/{chat_id}/history",
                "test_chat": "/chat/test",
                "flutter_chat": "/chat"
            }
        }
    }

# Endpoint for Flutter app
@app.post("/chat")
async def flutter_chat(request: ChatRequest):
    """Handle chat requests from Flutter app"""
    try:
        logging.info(f"Processing chat request for user {request.user_id}")
        
        # Create or get chat session
        try:
            session_id = await db.create_chat_session(request.user_id)
        except Exception as e:
            if "duplicate key error" in str(e):
                # If session already exists, get the existing session
                chat = await db.get_chat_session(request.user_id)
                session_id = chat["session_id"]
            else:
                raise
        
        # Add user message to chat
        await db.add_message(session_id, request.user_id, request.message, "user")
        
        # Get chatbot response
        if not chatbot:
            raise Exception("Chatbot not initialized")
            
        response = chatbot.get_response(request.message, request.user_id)
        
        # Add bot response to chat
        await db.add_message(session_id, request.user_id, response, "assistant")
        
        logging.info(f"Chat response sent for user {request.user_id}")
        return {"response": response}
        
    except Exception as e:
        logging.error(f"Error in /chat endpoint: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail={
                "message": "An error occurred while processing your request",
                "error": str(e)
            }
        )

# Test chat endpoint
@app.post("/chat/test")
async def test_chat(message: Message):
    try:
        if not chatbot:
            raise HTTPException(status_code=500, detail="Chatbot not initialized")
            
        # Create a test user if not exists
        test_user_id = "test-user-123"
        user = await db.get_user(test_user_id)
        if not user:
            await db.create_user({
                "name": "Test User",
                "email": "test@example.com",
                "phone": "1234567890",
                "age": 25,
                "gender": "other",
                "preferences": {"loves": [], "dislikes": [], "interests": []}
            })
        
        # Create a chat session
        chat_result = await db.create_chat_session(test_user_id)
        chat_id = str(chat_result.inserted_id)
        
        # Get chatbot response
        bot_response = chatbot.get_response(chat_id, message.content)
        
        # Store messages
        await db.add_message(chat_id, message.dict())
        await db.add_message(chat_id, {
            "content": bot_response,
            "is_user": False,
            "emotion": chatbot.emotion_handler.detect_emotion(bot_response)
        })
        
        return {
            "chat_id": chat_id,
            "user_message": message.content,
            "bot_response": bot_response
        }
    except Exception as e:
        logger.error(f"Error in test chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# User endpoints
@app.post("/users/")
async def create_user(user: UserCreate):
    try:
        result = await db.create_user(user.dict())
        return {"user_id": str(result.inserted_id)}
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    try:
        user = await db.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Chat endpoints
@app.post("/chat/{user_id}")
async def create_chat(user_id: str):
    try:
        result = await db.create_chat_session(user_id)
        return {"chat_id": str(result.inserted_id)}
    except Exception as e:
        logger.error(f"Error creating chat: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/chat/{chat_id}/message")
async def send_message(chat_id: str, message: Message):
    try:
        if not chatbot:
            raise HTTPException(status_code=500, detail="Chatbot not initialized")
            
        # Get chatbot response
        bot_response = chatbot.get_response(chat_id, message.content)
        
        # Store user message
        await db.add_message(chat_id, message.dict())
        
        # Store bot response
        bot_message = Message(
            content=bot_response,
            is_user=False,
            emotion=chatbot.emotion_handler.detect_emotion(bot_response)
        )
        await db.add_message(chat_id, bot_message.dict())
        
        return {"response": bot_response}
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/chat/{chat_id}/history")
async def get_chat_history(chat_id: str, limit: int = 50):
    try:
        history = await db.get_chat_history(chat_id, limit)
        if not history:
            raise HTTPException(status_code=404, detail="Chat history not found")
        return history
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
