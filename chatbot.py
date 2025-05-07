from openai import OpenAI
import os
from dotenv import load_dotenv
import time
from datetime import datetime
import json
from emotion_handler import EmotionHandler

load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not client:
    raise ValueError("OpenAI API key is missing!")
print(f"🟢 API Key loaded: {client.api_key[:5]}...")

emotion_handler = EmotionHandler()
print("🟢 EmotionHandler initialized")

class EllaChatbot:
    def __init__(self):
        self.model_name = "gpt-3.5-turbo"
        self.user_memory = {}
        self.emotion_handler = EmotionHandler()

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🟢 Chatbot instance created")

        # System prompt
        self.system_prompt = """You are Caroline, a friendly and empathetic AI companion. 
        Your responses should be warm, engaging, and tailored to the user's emotional state and preferences.
        Keep responses concise and natural, as if chatting with a friend."""

    def get_response(self, user_id, message):
        try:
            print(f"\n🟡 Processing message for user {user_id}: '{message}...'")
            
            # Detect emotion
            emotion = self.emotion_handler.detect_emotion(message)
            print(f"🟢 Detected emotion: {emotion}")
            
            # Get user preferences
            preferences = self.user_memory.get(user_id, {}).get("preferences", {"loves": []})
            print(f"🟢 User preferences: {preferences}")
            
            # Prepare messages for chat completion
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": message}
            ]
            
            # Add emotion and preferences context
            messages.insert(1, {
                "role": "system",
                "content": f"User's emotional state: {emotion}. User preferences: {json.dumps(preferences)}"
            })
            
            # Get response from OpenAI
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=150
            )
            
            bot_response = response.choices[0].message.content
            
            # Store the interaction
            self.store_interaction(user_id, message, bot_response, emotion)
            
            return bot_response
            
        except Exception as e:
            print(f"\n❌ Error in get_response: {str(e)}")
            return "I apologize, but I'm having trouble processing your message right now. Please try again in a moment."

    def store_interaction(self, user_id, user_message, bot_response, emotion):
        try:
            # Update user preferences if needed
            if user_id not in self.user_memory:
                self.user_memory[user_id] = {"preferences": {"loves": []}}
            
            msg_lower = user_message.lower()
            like_keywords = ["pasand", "psnd hai", "pasand", "like", "love", "fond of"]
            for keyword in like_keywords:
                if keyword in msg_lower:
                    parts = msg_lower.split(keyword)
                    item = parts[0].replace("mujhe", "").strip() if parts[0].strip() and "mujhe" in parts[0] else parts[-1].strip()
                    if item and item not in self.user_memory[user_id]["preferences"]["loves"]:
                        self.user_memory[user_id]["preferences"]["loves"].append(item)
                        print(f"🟢 Noted: {user_id} loves {item}")
                    break
            
            # Store in MongoDB (this will be handled by your db.py)
            from db import add_message
            add_message(user_id, {
                "content": user_message,
                "is_user": True,
                "emotion": emotion,
                "timestamp": datetime.utcnow()
            })
            
            add_message(user_id, {
                "content": bot_response,
                "is_user": False,
                "emotion": self.emotion_handler.detect_emotion(bot_response),
                "timestamp": datetime.utcnow()
            })
            
        except Exception as e:
            print(f"❌ Error storing interaction: {str(e)}")

    def get_user_preferences(self, user_id):
        return self.user_memory.get(user_id, {}).get("preferences", {
            "loves": [],
            "dislikes": [],
            "interests": []
        })

# if __name__ == "__main__":
#     chatbot = EllaChatbot()
#     user_id = "praga123"
#     print("🟡 Starting chat with user:", user_id)
    
#     # Preference tests
#     chatbot.get_response(user_id, "mujhe choc psnd hai")
#     time.sleep(2)
#     chatbot.get_response(user_id, "i'm fond of coffee yaar")
#     time.sleep(2)
#     chatbot.get_response(user_id, "mujhe tea pasand hai!!!")
#     time.sleep(2)
    
#     # Flirty tests
#     response = chatbot.get_response(user_id, "tumpe choc khane ko hai???")
#     print(f"Aradhya: {response}")
#     time.sleep(2)
#     chatbot.get_response(user_id, "you're looking hot today")
#     time.sleep(2)
    
#     # Emotional tests
#     chatbot.get_response(user_id, "i'm so tired yaar…")
#     time.sleep(2)
#     chatbot.get_response(user_id, "yayy i got a promotion!")
#     time.sleep(2)
    
#     # Casual/Random tests
#     chatbot.get_response(user_id, "kya chal raha hai?")
#     time.sleep(2)
#     chatbot.get_response(user_id, "random thought: cats are weird")
#     time.sleep(2)
