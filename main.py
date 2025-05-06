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
from pydantic import BaseModel
from chatbot import EllaChatbot

app = FastAPI()
chatbot = EllaChatbot()

class ChatRequest(BaseModel):
    user_id: str
    message: str

@app.post("/chat")
def chat(request: ChatRequest):
    try:
        response = chatbot.get_response(request.user_id, request.message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"message": "Caroline Chatbot API is running!"}
