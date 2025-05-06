from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict
import uvicorn
from chatbot import EllaChatbot
import time

app = FastAPI(title="Chatbot API", description="API for Ella Chatbot")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
print("🟢 CORS middleware added")

# Init chatbot
chatbot = EllaChatbot()
print("🟢 EllaChatbot initialized")

# Global metrics
start_time = time.time()
request_count = 0

# Request/Response Models
class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    emotion: str
    cost: float

class HealthResponse(BaseModel):
    status: str
    uptime: float
    request_count: int
    chatbot_initialized: bool
    memory_usage: Dict[str, int]
    last_error: Optional[str] = None

# CHAT Endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    global request_count
    request_count += 1
    print(f"\n📥 Received POST /chat request #{request_count}")
    print(f"➡️  user_id: {request.user_id}")
    print(f"➡️  message: {request.message}")

    # Time the full processing
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

# HEALTH Endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    print("\n📥 Received GET /health request")
    try:
        uptime = time.time() - start_time
        memory_usage = {
            "total_users": len(chatbot.user_memory),
            "cached_embeddings": len(chatbot.embedding_cache),
            "cached_responses": len(chatbot.response_cache)
        }

        print("🩺 Status: healthy")
        print(f"⏱️ Uptime: {uptime:.2f}s")
        print(f"📊 Memory: {memory_usage}")

        return HealthResponse(
            status="healthy",
            uptime=uptime,
            request_count=request_count,
            chatbot_initialized=True,
            memory_usage=memory_usage
        )
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            uptime=time.time() - start_time,
            request_count=request_count,
            chatbot_initialized=False,
            memory_usage={},
            last_error=str(e)
        )

# Run server
if __name__ == "__main__":
    print("🚀 Starting FastAPI server on http://0.0.0.0:8000")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
