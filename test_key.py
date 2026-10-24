import os
from dotenv import load_dotenv

load_dotenv()

print("OPENAI_API_KEY loaded:", bool(os.getenv("OPENAI_API_KEY")))
print("Key starts with:", (os.getenv("OPENAI_API_KEY") or "")[:5])