from fastapi import FastAPI, Request
from pydantic import BaseModel
from chatbot import EllaChatbot
import uvicorn
from main import app

app = FastAPI()
bot = EllaChatbot()

class MessageRequest(BaseModel):
    user_id: str
    message: str

@app.post("/chat")
async def chat_with_aradhya(request: MessageRequest):
    response = bot.get_response(request.user_id, request.message)
    return {"response": response}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

