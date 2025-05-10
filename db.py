from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel, ASCENDING
from datetime import datetime
import os
from dotenv import load_dotenv
import certifi
import logging
import time
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# MongoDB connection string
MONGODB_URL = os.getenv("MONGODB_URL")
if not MONGODB_URL:
    raise ValueError("MONGODB_URL environment variable is not set")

# Initialize MongoDB client
client = None
db = None

async def startup_db():
    """Initialize database connection and create indexes"""
    try:
        global client, db
        client = AsyncIOMotorClient(MONGODB_URL, tlsCAFile=certifi.where())
        db = client.get_database()
        
        # Test connection
        await db.command("ping")
        logger.info("Successfully connected to MongoDB")
        
        # Create indexes
        await init_db()
        logger.info("Database initialization completed")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

# Collections
def get_collections():
    if db is None:
        raise RuntimeError("Database not initialized. Call startup_db() first.")
    return {
        "users": db.users,
        "chats": db.chats,
        "messages": db.messages
    }

# Create indexes
async def init_db():
    try:
        collections = get_collections()
        
        # Users collection indexes
        await collections["users"].create_indexes([
            IndexModel([("email", ASCENDING)], unique=True),
            IndexModel([("phone", ASCENDING)], unique=True)
        ])
        logger.info("Created indexes for users collection")
        
        # Chats collection indexes
        await collections["chats"].create_indexes([
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("created_at", ASCENDING)])
        ])
        logger.info("Created indexes for chats collection")
        
        # Messages collection indexes
        await collections["messages"].create_indexes([
            IndexModel([("chat_id", ASCENDING)]),
            IndexModel([("timestamp", ASCENDING)])
        ])
        logger.info("Created indexes for messages collection")
        
        # Create test user if no users exist
        if await collections["users"].count_documents({}) == 0:
            await create_user({
                "name": "Test User",
                "email": "test@example.com",
                "phone": "1234567890",
                "age": 25,
                "gender": "other",
                "preferences": {
                    "loves": [],
                    "dislikes": [],
                    "interests": []
                }
            })
            logger.info("Created test user")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

# Database operations
async def create_user(user_data):
    try:
        collections = get_collections()
        user_data["created_at"] = datetime.utcnow()
        user_data["last_active"] = datetime.utcnow()
        
        # Ensure required fields
        if "deviceId" not in user_data:
            raise ValueError("deviceId is required")
            
        # Set default values if not provided
        if "name" not in user_data:
            user_data["name"] = "Guest"
        if "email" not in user_data:
            user_data["email"] = f"guest-{user_data['deviceId']}@placeholder.com"
            
        result = await collections["users"].insert_one(user_data)
        logger.info(f"Created user with ID: {result.inserted_id}")
        return result
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise

async def get_user(user_id):
    try:
        collections = get_collections()
        return await collections["users"].find_one({"_id": user_id})
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        raise

async def update_user(user_id, update_data):
    try:
        collections = get_collections()
        update_data["last_active"] = datetime.utcnow()
        result = await collections["users"].update_one(
            {"_id": user_id},
            {"$set": update_data}
        )
        logger.info(f"Updated user: {user_id}")
        return result
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise

async def create_chat_session(user_id: str) -> str:
    """Create a new chat session for a user"""
    try:
        collections = get_collections()
        if not collections:
            raise Exception("Database not initialized")

        # Generate a unique session ID using timestamp and random string
        session_id = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        chat_data = {
            "user_id": user_id,
            "session_id": session_id,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "messages": []
        }
        
        result = await collections["chats"].insert_one(chat_data)
        if not result.inserted_id:
            raise Exception("Failed to create chat session")
            
        return session_id
    except Exception as e:
        logging.error(f"Error creating chat session: {str(e)}")
        raise

async def add_message(chat_id: str, user_id: str, content: str, role: str):
    """Add a message to a chat session"""
    try:
        collections = get_collections()
        message_data = {
            "chat_id": chat_id,
            "user_id": user_id,
            "content": content,
            "role": role,
            "timestamp": datetime.utcnow()
        }
        
        result = await collections["messages"].insert_one(message_data)
        
        # Update chat session's last_activity
        await collections["chats"].update_one(
            {"session_id": chat_id},
            {"$set": {"last_activity": datetime.utcnow()}}
        )
        
        logging.info(f"Added message to chat: {chat_id}")
        return result
    except Exception as e:
        logging.error(f"Error adding message: {str(e)}")
        raise

async def get_chat_history(chat_id, limit=50):
    try:
        collections = get_collections()
        cursor = collections["messages"].find(
            {"chat_id": chat_id}
        ).sort("timestamp", -1).limit(limit)
        
        messages = await cursor.to_list(length=limit)
        return list(reversed(messages))  # Return in chronological order
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}")
        raise

async def get_chat_session(user_id: str):
    """Get the most recent chat session for a user"""
    try:
        collections = get_collections()
        chat = await collections["chats"].find_one(
            {"user_id": user_id},
            sort=[("last_activity", -1)]
        )
        if not chat:
            raise Exception(f"No chat session found for user {user_id}")
        return chat
    except Exception as e:
        logging.error(f"Error getting chat session: {str(e)}")
        raise

async def get_user_by_device_id(device_id):
    try:
        collections = get_collections()
        return await collections["users"].find_one({"deviceId": device_id})
    except Exception as e:
        logger.error(f"Error getting user by device ID: {str(e)}")
        raise

async def update_user_by_device_id(device_id, update_data):
    try:
        collections = get_collections()
        update_data["last_active"] = datetime.utcnow()
        result = await collections["users"].update_one(
            {"deviceId": device_id},
            {"$set": update_data}
        )
        logger.info(f"Updated user with device ID: {device_id}")
        return result
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise 