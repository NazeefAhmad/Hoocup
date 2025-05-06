import random

class EmotionHandler:
    def __init__(self):
        self.emotion_keywords = {
            "happy": ["excited", "amazing", "fantastic", "great", "love", "joy"],
            "sad": ["upset", "hurt", "lonely", "cry", "depressed", "bad"],
            "angry": ["mad", "frustrated", "hate", "annoyed", "furious"],
            "neutral": []
        }

    def detect_emotion(self, text):
        """Detect emotion from user message."""
        text_lower = text.lower()
        for emotion, keywords in self.emotion_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return emotion
        return "neutral"

    def apply_emotion(self, bot_response, detected_emotion):
        """Modify bot response tone based on detected emotion."""
        if detected_emotion == "happy":
            return f"{bot_response} ✨ OMG, I love that energy!"
        elif detected_emotion == "sad":
            return f"{bot_response} 💖 Hey, you got this! I'm here for you."
        elif detected_emotion == "angry":
            return f"{bot_response} 😤 Okay, deep breaths! What's really bothering you?"
        return bot_response  # Neutral case


