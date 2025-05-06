from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
client = MongoClient(MONGODB_URL)
db = client.chatbot_db

# Collections
users = db.users
chats = db.chats

# User operations
def create_user(user_data):
    user_data["created_at"] = datetime.utcnow()
    user_data["last_active"] = datetime.utcnow()
    return users.insert_one(user_data)

def get_user(user_id):
    return users.find_one({"_id": user_id})

def update_user(user_id, update_data):
    update_data["last_active"] = datetime.utcnow()
    return users.update_one({"_id": user_id}, {"$set": update_data})

# Chat operations
def create_chat_session(user_id):
    chat_data = {
        "user_id": user_id,
        "messages": [],
        "session_id": str(datetime.utcnow().timestamp()),
        "started_at": datetime.utcnow(),
        "last_message_at": datetime.utcnow()
    }
    return chats.insert_one(chat_data)

def add_message(chat_id, message_data):
    message_data["timestamp"] = datetime.utcnow()
    return chats.update_one(
        {"_id": chat_id},
        {
            "$push": {"messages": message_data},
            "$set": {"last_message_at": datetime.utcnow()}
        }
    )

def get_chat_history(chat_id, limit=50):
    return chats.find_one(
        {"_id": chat_id},
        {"messages": {"$slice": [-limit, limit]}}
    ) 