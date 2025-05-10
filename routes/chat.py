from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict
import time
from shared import chatbot

router = APIRouter(prefix="/chat", tags=["chat"])

# Request/Response Models
class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    emotion: str
    cost: float

@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    print(f"\n📥 Received POST /chat request")
    print(f"➡️  user_id: {request.user_id}")
    print(f"➡️  message: {request.message}")

    start_time = time.time()

    try:
        # Time the response generation
        response_start = time.time()
        response = chatbot.get_response(request.user_id, request.message)
        response_time = time.time() - response_start
        print(f"🕑 Response generation took: {response_time:.2f} seconds")

        # Time the emotion detection
        emotion_start = time.time()
        emotion = chatbot.emotion_handler.detect_emotion(request.message)
        emotion_time = time.time() - emotion_start
        print(f"🕑 Emotion detection took: {emotion_time:.2f} seconds")

        # Time the cost calculation
        cost_start = time.time()
        cost = chatbot.total_cost
        cost_time = time.time() - cost_start
        print(f"🕑 Cost calculation took: {cost_time:.2f} seconds")

        total_time = time.time() - start_time
        print(f"⏱️ Total request processing time: {total_time:.2f} seconds")

        print(f"🧠 Emotion: {emotion}")
        print(f"💬 Response: {response}")
        print(f"💰 Total cost so far: ${cost:.6f}")

        return ChatResponse(response=response, emotion=emotion, cost=cost)

    except Exception as e:
        print(f"❌ Error in /chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 