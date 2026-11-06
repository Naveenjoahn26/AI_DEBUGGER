import urllib.request
import json
import os
from dotenv import load_dotenv

load_dotenv("D:/Prograamming/RAG/AI Debugger/.env")
api_key = os.getenv("GROQ_API_KEY")

req = urllib.request.Request(
    'https://api.groq.com/openai/v1/models', 
    headers={'Authorization': f'Bearer {api_key}'}
)
try:
    resp = urllib.request.urlopen(req).read().decode('utf-8')
    data = json.loads(resp)['data']
    for model in data:
        print(model['id'])
except Exception as e:
    print(f"Error: {e}")
