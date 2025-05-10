from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List
import time
from shared import chatbot

router = APIRouter(prefix="/system", tags=["system"])

# Request Models
class AnalyticsRequest(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    user_id: Optional[str] = None

class SystemConfigRequest(BaseModel):
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    model_name: Optional[str] = None

class BatchProcessRequest(BaseModel):
    user_ids: List[str]
    operation: str  # "update", "delete", "export"

class HealthResponse(BaseModel):
    status: str
    uptime: float
    request_count: int
    chatbot_initialized: bool
    memory_usage: Dict[str, int]
    last_error: Optional[str] = None

@router.get("/health", response_model=HealthResponse)
async def health_check():
    print("\n📥 Received GET /health request")
    try:
        uptime = time.time() - getattr(chatbot, 'start_time', time.time())
        memory_usage = {
            "total_users": len(chatbot.user_memory),
            "cached_embeddings": len(getattr(chatbot, 'embedding_cache', {})),
            "cached_responses": len(chatbot.response_cache)
        }

        print("🩺 Status: healthy")
        print(f"⏱️ Uptime: {uptime:.2f}s")
        print(f"📊 Memory: {memory_usage}")

        return HealthResponse(
            status="healthy",
            uptime=uptime,
            request_count=getattr(chatbot, 'request_count', 0),
            chatbot_initialized=True,
            memory_usage=memory_usage
        )
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            uptime=time.time() - getattr(chatbot, 'start_time', time.time()),
            request_count=getattr(chatbot, 'request_count', 0),
            chatbot_initialized=False,
            memory_usage={},
            last_error=str(e)
        )

@router.get("/analytics")
async def get_analytics(request: AnalyticsRequest):
    try:
        # Get basic metrics
        metrics = {
            "total_users": len(chatbot.user_memory),
            "total_requests": getattr(chatbot, 'request_count', 0),
            "uptime": time.time() - getattr(chatbot, 'start_time', time.time()),
            "average_response_time": chatbot.get_average_response_time(),
            "total_cost": chatbot.total_cost
        }
        
        # Get user-specific metrics if user_id provided
        if request.user_id:
            user_metrics = chatbot.get_user_metrics(request.user_id)
            metrics["user_metrics"] = user_metrics
            
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/config")
async def update_system_config(request: SystemConfigRequest):
    try:
        if request.max_tokens:
            chatbot.max_tokens = request.max_tokens
        if request.temperature:
            chatbot.temperature = request.temperature
        if request.model_name:
            chatbot.model_name = request.model_name
            
        return {"message": "System configuration updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch")
async def batch_process(request: BatchProcessRequest):
    try:
        results = []
        for user_id in request.user_ids:
            if request.operation == "update":
                # Update user preferences and memory
                chatbot.refresh_user_memory(user_id)
                results.append({"user_id": user_id, "status": "updated"})
            elif request.operation == "delete":
                # Delete user data
                chatbot.clear_user_memory(user_id)
                results.append({"user_id": user_id, "status": "deleted"})
            elif request.operation == "export":
                # Export user data
                user_data = chatbot.export_user_data(user_id)
                results.append({"user_id": user_id, "data": user_data})
                
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset")
async def reset_system():
    try:
        # Reset chatbot state
        chatbot.reset()
        # Reset global metrics
        chatbot.request_count = 0
        chatbot.start_time = time.time()
        
        return {"message": "System reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 