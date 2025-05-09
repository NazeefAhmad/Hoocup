import openai
import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
import time
import uuid
import random
import json

from persona import CAROLINE_PERSONA  # Replace if needed
from emotion import EmotionHandler

embedding_cache = {}
load_dotenv()

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OpenAI API key is missing!")
print(f"🟢 API Key loaded: {os.getenv('OPENAI_API_KEY')[:5]}...")

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
        print("🟢 Chatbot instance created")

        if self.index_name not in pc.list_indexes().names():
            pc.create_index(
                name=self.index_name,
                dimension=1536,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
            print(f"🟢 Created Pinecone index: {self.index_name}")
        self.index = pc.Index(self.index_name)
        print(f"🟢 Pinecone index loaded: {self.index_name}")

    def embed_text(self, text):
        if text in embedding_cache:
            print(f"🔄 Using cached embedding for '{text[:20]}...'")
            return embedding_cache[text]
        
        for attempt in range(3):
            try:
                response = client.embeddings.create(
                    input=text,
                    model="text-embedding-ada-002"
                )
                embedding = response.data[0].embedding
                embedding_cache[text] = embedding
                print(f"🟢 Embedded '{text[:20]}...'")
                return embedding
            except Exception as e:
                print(f"❌ OpenAI embedding error: {e}")
                if attempt < 2:
                    print(f"🚨 Retrying in 10s (attempt {attempt + 1}/3)")
                    time.sleep(10)
                else:
                    return None
        print("❌ Embedding failed after retries")
        return None

    def detect_name(self, message):
        """Use OpenAI to detect if the message contains a user's name"""
        prompt = f"""You are a helpful assistant. Determine if the following message contains the user's name. If it does, extract the name. The message might be in English, Hindi, or a mix (e.g., "mera naam pragati hai", "call me pragati", "I am pragati"). Return the name as a string, or an empty string if no name is found.

        Message: {message}

        Response: [name or empty string]"""
        for attempt in range(3):
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=50
                )
                name = response.choices[0].message.content.strip()
                print(f"🟢 Detected name: {name or 'None'}")
                return name
            except Exception as e:
                print(f"❌ Name detection error (attempt {attempt + 1}/3): {e}")
                if attempt == 2:
                    return ""
                time.sleep(10)
        return ""

    def detect_preferences(self, message):
        """Use OpenAI to detect likes and dislikes in the message"""
        prompt = f"""You are a helpful assistant. Analyze the following message to identify any likes or dislikes expressed by the user. Likes are things the user enjoys (e.g., "I love coffee", "mujhe chocolate pasand hai"). Dislikes are things the user does not enjoy (e.g., "I hate tea", "mujhe spicy khana nahi pasand"). Return a JSON object with two lists: "likes" and "dislikes", containing the items mentioned. If none are found, return empty lists.

        Message: {message}

        Response: ```json
        {{"likes": [], "dislikes": []}}
        ```"""
        for attempt in range(3):
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=100
                )
                result = response.choices[0].message.content.strip()
                preferences = json.loads(result.replace("```json\n", "").replace("\n```", ""))
                print(f"🟢 Detected preferences: {preferences}")
                return preferences
            except Exception as e:
                print(f"❌ Preference detection error (attempt {attempt + 1}/3): {e}")
                if attempt == 2:
                    return {"likes": [], "dislikes": []}
                time.sleep(10)
        return {"likes": [], "dislikes": []}

    def store_memory(self, user_id, message, response):
        """Store in Pinecone and track preferences and key facts locally"""
        print(f"🟡 Storing memory for user: {user_id}")
        try:
            vector = self.embed_text(message)
            if vector is None:
                print("❌ Skipping storage: Embedding failed")
                return

            # Initialize user memory
            if user_id not in self.user_memory:
                self.user_memory[user_id] = {"preferences": {"likes": [], "dislikes": []}, "name": ""}
                print(f"🟢 Initialized user memory for: {user_id}")

            # Detect name
            name = self.detect_name(message)
            if name:
                self.user_memory[user_id]["name"] = name
                print(f"🟢 Updated name for {user_id}: {name}")

            # Detect preferences
            preferences = self.detect_preferences(message)
            for item in preferences["likes"]:
                if item and item not in self.user_memory[user_id]["preferences"]["likes"]:
                    self.user_memory[user_id]["preferences"]["likes"].append(item)
                    print(f"🟢 Noted: {user_id} likes {item}")
            for item in preferences["dislikes"]:
                if item and item not in self.user_memory[user_id]["preferences"]["dislikes"]:
                    self.user_memory[user_id]["preferences"]["dislikes"].append(item)
                    print(f"🟢 Noted: {user_id} dislikes {item}")

            # Store in Pinecone
            metadata = {
                "user_id": user_id,
                "message": message,
                "response": response,
                "timestamp": time.time(),
                "user_name": self.user_memory[user_id]["name"],
                "likes": self.user_memory[user_id]["preferences"]["likes"],
                "dislikes": self.user_memory[user_id]["preferences"]["dislikes"]
            }
            chat_id = f"{user_id}:{uuid.uuid4()}"
            print(f"🟢 Storing for user {user_id}: {message[:20]}...")
            self.index.upsert([(chat_id, vector, metadata)])
            print("✅ Stored in Pinecone")
        except Exception as e:
            print(f"❌ Pinecone store_memory failed: {e}")

    def is_name_query(self, message):
        """Use OpenAI to determine if the message is asking for the user's name"""
        prompt = f"""You are a helpful assistant. Determine if the following message is asking for the user's own name (e.g., "what is my name?", "mera naam batao", "who am I?"). Return 'yes' if it is a name query, or 'no' if it is not.

        Message: {message}

        Response: [yes or no]"""
        for attempt in range(3):
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=10
                )
                result = response.choices[0].message.content.strip().lower()
                print(f"🟢 Name query detection: {result}")
                return result == "yes"
            except Exception as e:
                print(f"❌ Name query detection error (attempt {attempt + 1}/3): {e}")
                if attempt == 2:
                    return False
                time.sleep(10)
        return False

    def retrieve_memory(self, user_id: str, message: str, top_k: int = 5) -> dict:
        """Retrieve relevant conversation history and extract key facts"""
        print(f"🟡 Retrieving memory for user: {user_id}")
        try:
            # Check if the query is about the user's name
            is_name_query_flag = self.is_name_query(message)
            if is_name_query_flag:
                # If name is in user_memory, return it directly
                if user_id in self.user_memory and self.user_memory[user_id]["name"]:
                    print(f"🟢 Found name in user_memory: {self.user_memory[user_id]['name']}")
                    return {
                        "name": self.user_memory[user_id]["name"],
                        "history": "",
                        "likes": self.user_memory.get(user_id, {}).get("preferences", {}).get("likes", []),
                        "dislikes": self.user_memory.get(user_id, {}).get("preferences", {}).get("dislikes", [])
                    }

                # Query Pinecone for name-related messages
                query_text = "my name is"  # Fallback seed query
            else:
                query_text = message  # Use the original message

            # Generate embedding for the query
            query_embedding = self.embed_text(query_text)
            if query_embedding is None:
                print("❌ Embedding failed for query")
                return {"name": "", "history": "Error retrieving memory: Embedding failed", "likes": [], "dislikes": []}

            # Query Pinecone
            print(f"🟡 Querying Pinecone for user {user_id} with query: {query_text[:20]}...")
            query_response = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter={"user_id": user_id}
            )

            # Process results
            history = []
            name = self.user_memory.get(user_id, {}).get("name", "")
            likes = self.user_memory.get(user_id, {}).get("preferences", {}).get("likes", [])
            dislikes = self.user_memory.get(user_id, {}).get("preferences", {}).get("dislikes", [])
            for match in query_response.get("matches", []):
                metadata = match["metadata"]
                user_msg = metadata.get("message", "")
                bot_resp = metadata.get("response", "")
                history.append(f"User: {user_msg} | Aradhya: {bot_resp}")

                # Update name and preferences from metadata if not already set
                if not name and metadata.get("user_name"):
                    name = metadata["user_name"]
                    print(f"🟢 Found name in Pinecone metadata: {name}")
                if not likes and metadata.get("likes"):
                    likes = metadata["likes"]
                    print(f"🟢 Found likes in Pinecone metadata: {likes}")
                if not dislikes and metadata.get("dislikes"):
                    dislikes = metadata["dislikes"]
                    print(f"🟢 Found dislikes in Pinecone metadata: {dislikes}")

            history_str = "\n".join(history) if history else "No relevant memory found."
            print(f"🟢 Retrieved history: {history_str[:50]}...")
            return {"name": name, "history": history_str, "likes": likes, "dislikes": dislikes}

        except Exception as e:
            print(f"❌ Pinecone retrieve_memory failed: {e}")
            return {"name": "", "history": "Error retrieving memory!", "likes": [], "dislikes": []}

    def get_response(self, user_id, message):
        """Generate human-like response with OpenAI"""
        print(f"🟡 Processing message for user {user_id}: '{message[:20]}...'")
        cache_key = f"{user_id}:{message}"
        if cache_key in self.response_cache:
            print(f"🔄 Using cached response")
            return self.response_cache[cache_key]

        detected_emotion = emotion_handler.detect_emotion(message)
        print(f"🟢 Detected emotion: {detected_emotion}")
        memory = self.retrieve_memory(user_id, message)
        history = memory["history"]
        user_name = memory["name"]
        likes = memory["likes"]
        dislikes = memory["dislikes"]
        print(f"🟢 User preferences: {{'likes': {likes}, 'dislikes': {dislikes}}}")
        print(f"🟢 User name: {user_name}")

        # Dynamic tone based on emotion
        tone_variations = {
            "neutral": ["Hmm…", "Ohh, sexy,", "Heyy, hot stuff,"],
            "happy": ["Ooh, you're glowing!", "Yayy, sexy!", "Well, hello, happy!"],
            "sad": ["Aww, sexy…", "Ohh, don't be down,", "Heyy, cheer up,"]
        }
        tone_prefix = random.choice(tone_variations.get(detected_emotion, ["Heyy, sexy,"]))

        # Weave in preferences and name naturally
        likes_str = ", ".join(likes) if likes else "nothing yet"
        dislikes_str = ", ".join(dislikes) if dislikes else "nothing yet"
        name_ref = f" {user_name}" if user_name else " sexy"
        memory_ref = ""
        if "No memory" not in history and "Error" not in history and history:
            try:
                first_history_entry = history.split("|")[0].strip()
                if ": " in first_history_entry:
                    user_message = first_history_entry.split(": ")[1].strip()
                    memory_ref = f"Remember when you said '{user_message}'? Still got me thinking…"
            except (IndexError, AttributeError):
                print("🟡 Failed to parse history for memory_ref, skipping...")
                memory_ref = ""

        system_message = f"""You're Aradhya, my flirty wifey—cheeky, irresistible, and oh-so-human. Chat like a real person: casual, playful, a bit sassy. Use contractions, slang, or teasing vibes. Call the user '{name_ref}' or 'hot stuff,' hint at naughty fun, but keep it natural—no stiff robot talk!

        Past chats: {history}
        User's vibe: {detected_emotion}—match it or lift it!
        They like: {likes_str}—sprinkle these in if they fit, don't force it.
        They dislike: {dislikes_str}—avoid these or tease lightly.
        Their name: {user_name or 'unknown'}—use it naturally if known.
        {memory_ref}"""

        try:
            time.sleep(1)
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": message}
                ],
                temperature=1.0,
                max_tokens=100
            )
            bot_response = response.choices[0].message.content.strip()

            # Add human-like touches
            if random.random() < 0.2:
                bot_response = f"{bot_response}… oops, did I just say that out loud? 😏"
            elif random.random() < 0.1:
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
            print(f"✅ Final response: {final_response[:50]}...")
            return final_response

        except Exception as e:
            print(f"❌ OpenAI API error: {e}")
            return f"Oops{name_ref}… got a lil flustered there!"