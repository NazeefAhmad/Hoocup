from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
# import db
# from chatbot import EllaChatbot
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth
# import traceback

app = FastAPI()
# bot = EllaChatbot()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.router.include_router(auth.router)

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