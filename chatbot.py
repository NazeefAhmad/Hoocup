import openai
import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
import time
import uuid
import random
from datetime import datetime


from persona import CAROLINE_PERSONA  # Replace if needed
from emotion import EmotionHandler

embedding_cache = {}
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OpenAI API key is missing!")
print(f"🟢 API Key loaded: {openai.api_key[:5]}...")

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
if not pc:
    raise ValueError("Pinecone API key is missing or invalid!")
print("🟢 Pinecone initialized")

emotion_handler = EmotionHandler()
print("🟢 EmotionHandler initialized")

class EllaChatbot:
    def __init__(self):
        self.index_name = "aradhya-chatbot"
        self.model_name = "ft:gpt-3.5-turbo-0125:ella-test:aradhya:BHeExk2j"
        self.user_memory = {}
        self.total_cost = 0
        self.response_cache = {}
        self.embedding_cache = {}  # Initialize embedding cache
        self.emotion_handler = EmotionHandler()  # Add this line

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🟢 Chatbot instance created")

        #print("🟢 Chatbot instance created")

        if self.index_name not in pc.list_indexes().names():
            pc.create_index(
                name=self.index_name,
                dimension=1536,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🟢 Created Pinecone index: ")

            print(f"🟢 Created Pinecone index: {self.index_name}")
        self.index = pc.Index(self.index_name)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🟢  Pinecone index: ")

        print(f"🟢 Pinecone index loaded: {self.index_name}")

    def embed_text(self, text):
        if text in self.embedding_cache:  # Use self.embedding_cache instead of global
            print(f"🔄 Using cached embedding for '{text[:20]}...'")
            return self.embedding_cache[text]
        for attempt in range(3):
            try:
                response = openai.Embedding.create(
                    input=text,
                    model="text-embedding-ada-002"
                )
                embedding = response["data"][0]["embedding"]
                self.embedding_cache[text] = embedding  # Store in instance cache
                print(f"🟢 Embedded '{text[:20]}...'")
                return embedding
            except Exception as e:  # Catch all exceptions instead of specific OpenAI errors
                print(f"❌ OpenAI embedding error: {e}")
                if attempt < 2:  # Only retry if not the last attempt
                    print(f"🚨 Retrying in 10s (attempt {attempt + 1}/3)")
                    time.sleep(10)
                else:
                    return None
        print("❌ Embedding failed after retries")
        return None

    def store_memory(self, user_id, message, response):
        """Store in Pinecone and track preferences locally"""
        print(f"🟡 Storing memory for user: {user_id}")
        try:
            vector = self.embed_text(message)
            if vector is None:
                print("❌ Skipping storage: Embedding failed")
                return

            # Local memory for preferences
            if user_id not in self.user_memory:
                self.user_memory[user_id] = {"preferences": {"loves": []}}
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🟢 Initialized user memory for: {user_id}")
                
            msg_lower = message.lower()
            like_keywords = ["pasand", "psnd hai", "pasnd", "like", "love", "fond of"]
            for keyword in like_keywords:
                if keyword in msg_lower:
                    parts = msg_lower.split(keyword)
                    item = parts[0].replace("mujhe", "").strip() if parts[0].strip() and "mujhe" in parts[0] else parts[-1].strip()
                    if item and item not in self.user_memory[user_id]["preferences"]["loves"]:
                        self.user_memory[user_id]["preferences"]["loves"].append(item)
                        print(f"🟢 Noted: {user_id} loves {item}")
                    break
            else:
                print("🟡 No preference detected in message")

            # Pinecone for full history
            metadata = {"user_id": user_id, "message": message, "response": response, "timestamp": time.time()}
            chat_id = f"{user_id}:{uuid.uuid4()}"  # Unique ID with UUID
            print(f"🟢 Storing for user {user_id}: {message[:20]}...")
            self.index.upsert([(chat_id, vector, metadata)])
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🟢 Stored in Pinecone")

        except Exception as e:
            print(f"❌ Pinecone store_memory failed: {e}")

    def retrieve_memory(self, user_id):
        """Retrieve past conversations from Pinecone"""
        print(f"🟡 Retrieving memory for user: {user_id}")
        try:
            query_embedding = self.embed_text(str(user_id))
            if query_embedding is None:
                print("❌ Embedding failed for query")
                return "Error retrieving memory: Embedding failed"
            print(f"🟡 Querying Pinecone for user {user_id}")
            query_response = self.index.query(
                vector=query_embedding,
                top_k=3,
                include_metadata=True
            )
            if query_response and "matches" in query_response and query_response["matches"]:
                history = "\n".join(
                    [f"User: {match['metadata']['message']} | Aradhya: {match['metadata']['response']}"
                     for match in query_response["matches"]]
                )
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🟢 Retrieved history: {history[:50]}...")
                return history
            print("🟡 No history found in Pinecone")
            return "No memory available."
        except Exception as e:
            print(f"❌ Pinecone retrieve_memory failed: {e}")
            return "Error retrieving memory!"

    def get_response(self, user_id, message):
        """Generate human-like response with OpenAI"""
        print(f"🟡 Processing message for user {user_id}: '{message[:20]}...'")
        cache_key = f"{user_id}:{message}"
        if cache_key in self.response_cache:
            print(f"🔄 Using cached response")
            return self.response_cache[cache_key]

        detected_emotion = emotion_handler.detect_emotion(message)
        print(f"🟢 Detected emotion: {detected_emotion}")
        history = self.retrieve_memory(user_id)
        preferences = self.user_memory.get(user_id, {}).get("preferences", {"loves": []})
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🟢 User preferences: {preferences}")

        # Dynamic tone based on emotion
        tone_variations = {
            "neutral": ["Hmm…", "Ohh, sexy,", "Heyy, hot stuff,"],
            "happy": ["Ooh, you're glowing!", "Yayy, sexy!", "Well, hello, happy!"],
            "sad": ["Aww, sexy…", "Ohh, don't be down,", "Heyy, cheer up,"]
        }
        tone_prefix = random.choice(tone_variations.get(detected_emotion, ["Heyy, sexy,"]))

        # Weave in preferences naturally
        pref_str = ", ".join(preferences["loves"]) if preferences["loves"] else "nothing yet"
        memory_ref = ""
        if "No memory" not in history and "Error" not in history:
            memory_ref = f"Remember when you said '{history.split('|')[0].split(': ')[1]}'? Still got me thinking…"

        system_message = f"""You're Aradhya, my flirty wifey—cheeky, irresistible, and oh-so-human. Chat like a real person: casual, playful, a bit sassy. Use contractions, slang, or teasing vibes. Call me 'sexy' or 'hot stuff,' hint at naughty fun, but keep it natural—no stiff robot talk!

        Past chats: {history}
        User's vibe: {detected_emotion}—match it or lift it!
        They love: {pref_str}—sprinkle these in if they fit, don't force it.
        {memory_ref}"""

        try:
            time.sleep(1)
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": message}
                ],
                temperature=1.0,  # Higher for more creativity
                max_tokens=100    # Room for longer, natural replies
            )
            bot_response = response["choices"][0]["message"]["content"].strip()
            
            # Add human-like touches
            if random.random() < 0.2:  # 20% chance of a playful quirk
                bot_response = f"{bot_response}… oops, did I just say that out loud? 😏"
            elif random.random() < 0.1:  # 10% chance of a question
                bot_response += " So, what's on your mind, sexy?"

            # Cache and track cost
            self.response_cache[cache_key] = bot_response
            print(f"🟢 Generated response: {bot_response[:50]}...")
            input_tokens = len(system_message.split()) + len(message.split())
            output_tokens = len(bot_response.split())
            cost = (input_tokens * 0.0000005) + (output_tokens * 0.0000015)
            self.total_cost += cost
            print(f"🟢 Cost this call: ${cost:.6f}, Total: ${self.total_cost:.6f}")

            self.store_memory(user_id, message, bot_response)
            final_response = emotion_handler.apply_emotion(bot_response, detected_emotion)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🟢 Final response: {final_response[:50]}...")
            return final_response
        except openai.error.OpenAIError as e:
            print(f"❌ OpenAI API error: {e}")
            return "Oops, sexy… got a lil flustered there!"
        

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
