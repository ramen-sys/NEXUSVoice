import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Read the API key from the environment variable we set
api_key = os.environ.get("GROQ_API_KEY")

if not api_key:
    print("ERROR: GROQ_API_KEY not found. Did you set it in this terminal session?")
else:
    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": "Say hello in 5 words"}
        ]
    )

    print("Groq replied:")
    print(response.choices[0].message.content)