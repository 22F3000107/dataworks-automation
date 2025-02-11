import os
import requests

AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")  # ✅ Correct way to access it

def call_llm(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {AIPROXY_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post("https://api.aiproxy.io/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        print("❌ ERROR:", e)
        return '{"error": "API request failed"}'
