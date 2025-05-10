from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
from shared import chatbot
from db import create_user, get_user_by_device_id, update_user_by_device_id

router = APIRouter(prefix="/users", tags=["users"])

# Request Models
class GuestUserRequest(BaseModel):
    deviceId: str
    deviceFingerprint: str

class UserDetailsRequest(BaseModel):
    deviceId: str
    name: str

class InterestRequest(BaseModel):
    deviceId: str
    interest: str

class UserSearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 10
    offset: Optional[int] = 0

@router.post("/guest")
async def register_guest_user(request: GuestUserRequest):
    try:
        # Check if user already exists
        existing_user = await get_user_by_device_id(request.deviceId)
        
        if existing_user:
            # Update fingerprint if needed
            if existing_user.get("deviceFingerprint") != request.deviceFingerprint:
                await update_user_by_device_id(request.deviceId, {
                    "deviceFingerprint": request.deviceFingerprint
                })
            return {"message": "Guest user already exists", "user": existing_user}
        
        # Create new guest user
        new_user = await create_user({
            "deviceId": request.deviceId,
            "deviceFingerprint": request.deviceFingerprint,
            "name": "Guest",
            "email": f"guest-{request.deviceId}@placeholder.com"
        })
        
        return {"message": "Guest user created successfully", "user": new_user}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/details")
async def update_user_details(request: UserDetailsRequest):
    try:
        if not request.deviceId or not request.name:
            raise HTTPException(status_code=400, detail="deviceId and name are required")
        
        # Check if user exists
        existing_user = await get_user_by_device_id(request.deviceId)
        
        if existing_user:
            # Update user details
            updated_user = await update_user_by_device_id(request.deviceId, {
                "name": request.name
            })
            return {"message": "User details updated", "user": updated_user}
        
        # Create new user if doesn't exist
        new_user = await create_user({
            "deviceId": request.deviceId,
            "name": request.name
        })
        
        return {"message": "User created successfully", "user": new_user}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/interest")
async def update_interest(request: InterestRequest):
    try:
        if not request.deviceId or not request.interest:
            raise HTTPException(status_code=400, detail="deviceId and interest are required")
        
        # Check if user exists
        existing_user = await get_user_by_device_id(request.deviceId)
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update interest
        updated_user = await update_user_by_device_id(request.deviceId, {
            "interest": request.interest
        })
        
        return {"message": "Interest updated", "user": updated_user}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
async def search_users(request: UserSearchRequest):
    try:
        # Search users based on query
        results = []
        for user_id, user_data in chatbot.user_memory.items():
            if (request.query.lower() in user_data.get("name", "").lower() or
                request.query.lower() in str(user_data.get("preferences", {})).lower()):
                results.append({
                    "user_id": user_id,
                    "name": user_data.get("name", ""),
                    "preferences": user_data.get("preferences", {})
                })
                
        # Apply pagination
        start = request.offset
        end = start + request.limit
        paginated_results = results[start:end]
        
        return {
            "total": len(results),
            "offset": request.offset,
            "limit": request.limit,
            "results": paginated_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/sessions")
async def get_user_sessions(user_id: str):
    try:
        sessions = chatbot.get_user_sessions(user_id)
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}/sessions/{session_id}")
async def delete_user_session(user_id: str, session_id: str):
    try:
        chatbot.delete_user_session(user_id, session_id)
        return {"message": "Session deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 