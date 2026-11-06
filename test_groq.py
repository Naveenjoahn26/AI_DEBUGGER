import os
from groq import Groq

api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)

models_to_try = [
    "llama3-groq-70b-8192-tool-use-preview",
    "gemma2-9b-it",
    "mixtral-8x7b-32768",
    "llama3-8b-8192"
]

for model in models_to_try:
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "hello"}
            ]
        )
        print(f"SUCCESS model {model}:")
        print(response.choices[0].message.content)
    except Exception as e:
        print(f"Error for model {model}: {e}")
