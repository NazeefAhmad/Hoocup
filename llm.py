import openai
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# def get_chat_response(prompt):
#     response = openai.ChatCompletion.create(
#         model="gpt-4o-mini",
#         messages=[{"role": "system", "content": prompt}],
#         api_key=OPENAI_API_KEY
#     )
#     return response["choices"][0]["message"]["content"]

def get_chat_response(messages):
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY")  # Ensure this is set
    )
    return response["choices"][0]["message"]["content"]