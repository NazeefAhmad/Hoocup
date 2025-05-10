from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import uvicorn
from routes import chat, users, system
from shared import chatbot  # Import shared instance

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

# Root health check endpoint
@app.get("/health")
async def root_health_check():
    """Redirect to system health check endpoint"""
    return RedirectResponse(url="/system/health")

# Include routers
app.include_router(chat.router)
app.include_router(users.router)
app.include_router(system.router)

# Run server
if __name__ == "__main__":
    print("🚀 Starting FastAPI server on http://0.0.0.0:8000")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
