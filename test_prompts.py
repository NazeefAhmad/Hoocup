# test_prompts.py
import time
from chatbot import EllaChatbot  # Import from chatbot.py

if __name__ == "__main__":
    chatbot = EllaChatbot()  # Initialize once
    user_id = "praga123"
    print("🟡 Starting chat with user:", user_id)
    
    # Preference tests
    chatbot.get_response(user_id, "mujhe choc psnd hai")
    time.sleep(2)
    chatbot.get_response(user_id, "i’m fond of coffee yaar")
    time.sleep(2)
    chatbot.get_response(user_id, "mujhe tea pasand hai!!!")
    time.sleep(2)
    
    # Flirty tests
    response = chatbot.get_response(user_id, "tumpe choc khane ko hai???")
    print(f"Aradhya: {response}")
    time.sleep(2)
    chatbot.get_response(user_id, "you’re looking hot today")
    time.sleep(2)
    
    # Emotional tests
    chatbot.get_response(user_id, "i’m so tired yaar…")
    time.sleep(2)
    chatbot.get_response(user_id, "yayy i got a promotion!")
    time.sleep(2)
    
    # Casual/Random tests
    chatbot.get_response(user_id, "kya chal raha hai?")
    time.sleep(2)
    chatbot.get_response(user_id, "random thought: cats are weird")
    time.sleep(2)