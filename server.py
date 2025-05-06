from fastapi import FastAPI, Request
from pydantic import BaseModel
from chatbot import EllaChatbot

app = FastAPI()
bot = EllaChatbot()

class MessageRequest(BaseModel):
    user_id: str
    message: str

@app.post("/chat")
async def chat_with_aradhya(request: MessageRequest):
    response = bot.get_response(request.user_id, request.message)
    return {"response": response}

