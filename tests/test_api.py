import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")
print(f"API Key present: {bool(api_key)}")

client = genai.Client(api_key=api_key)

print("Sending request to Gemini...")
try:
    # Test simple generation without tools
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents="Hello, say test passed!"
    )
    print("Response received:", response.text)
except Exception as e:
    print("API Call Failed:", e)