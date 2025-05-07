from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient, IndexModel, ASCENDING, DESCENDING
from datetime import datetime
import os
from dotenv import load_dotenv
import time

load_dotenv()

# MongoDB connection with retry logic
def get_mongodb_client(max_retries=3, retry_delay=1):
    MONGODB_URL = os.getenv("MONGODB_URL")
    if not MONGODB_URL:
        raise ValueError("MONGODB_URL environment variable is not set!")
    
    for attempt in range(max_retries):
        try:
            # Simple MongoDB client configuration
            client = MongoClient(
                MONGODB_URL,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            # Test the connection
            client.admin.command('ping')
            print("🟢 Successfully connected to MongoDB!")
            return client
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️ MongoDB connection attempt {attempt + 1} failed: {str(e)}")
                print(f"🔄 Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"❌ Failed to connect to MongoDB after {max_retries} attempts")
                raise

# Initialize MongoDB client
client = get_mongodb_client()
db = client.chatbot_db

# Collections
users = db.users
chats = db.chats

# Initialize database with indexes
def init_db():
    try:
        # Create indexes for users collection
        users.create_indexes([
            IndexModel([("email", ASCENDING)], unique=True),
            IndexModel([("phone", ASCENDING)], unique=True),
            IndexModel([("created_at", DESCENDING)]),
            IndexModel([("last_active", DESCENDING)])
        ])
        print("🟢 Created indexes for users collection")

        # Create indexes for chats collection
        chats.create_indexes([
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("started_at", DESCENDING)]),
            IndexModel([("last_message_at", DESCENDING)]),
            IndexModel([("session_id", ASCENDING)], unique=True)
        ])
        print("🟢 Created indexes for chats collection")

        # Create a test user if none exists
        if users.count_documents({}) == 0:
            test_user = {
                "name": "Test User",
                "email": "test@example.com",
                "phone": "1234567890",
                "age": 25,
                "gender": "other",
                "preferences": {"loves": [], "dislikes": [], "interests": []},
                "created_at": datetime.utcnow(),
                "last_active": datetime.utcnow()
            }
            users.insert_one(test_user)
            print("🟢 Created test user")

    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        raise

# Initialize the database
init_db()

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