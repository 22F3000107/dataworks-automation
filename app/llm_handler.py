import os
import requests
import logging

# Ensure AIPROXY_TOKEN is set as an environment variable
AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")
if not AIPROXY_TOKEN:
    raise ValueError("❌ Missing AI Proxy token. Set AIPROXY_TOKEN as an environment variable.")

# Logging setup
logging.basicConfig(level=logging.INFO)

def call_llm(prompt: str) -> str:
    """
    Calls the AI Proxy LLM (GPT-4o-Mini) with the given prompt and returns a JSON response.
    """
    headers = {
        "Authorization": f"Bearer {AIPROXY_TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that outputs only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 200  # Keep responses short to fit within AI Proxy's 20s limit
    }
    
    try:
        response = requests.post(
            "https://api.aiproxy.io/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=15  # Ensures request does not exceed 20s
        )
        
        response.raise_for_status()  # Raises an error for HTTP 4xx/5xx responses
        result = response.json()

        if "choices" in result and result["choices"]:
            return result["choices"][0]["message"]["content"]
        else:
            logging.error("❌ Unexpected LLM response format: %s", result)
            return '{"error": "Unexpected response format"}'

    except requests.exceptions.Timeout:
        logging.error("⏳ LLM request timed out. Reduce prompt length or retry.")
        return '{"error": "LLM request timed out"}'
    
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ LLM API request error: {str(e)}")
        return '{"error": "LLM processing failed"}'
