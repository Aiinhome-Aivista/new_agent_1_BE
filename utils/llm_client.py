import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

MISTRAL_LOCAL_URL = os.getenv("MISTRAL_LOCAL_URL", "http://122.163.121.176:3041")
MISTRAL_LOCAL_MODEL = os.getenv("MISTRAL_LOCAL_MODEL", "mistral-small:24b")

def query_llm(system_prompt, user_prompt, temperature=0.2, max_tokens=2048, json_mode=False):
    """
    Sends a chat completion request to the local Mistral LLM endpoint.
    If the endpoint is down, it returns None, enabling the orchestrator to fall back to static/heuristic mocks.
    """
    url = f"{MISTRAL_LOCAL_URL.rstrip('/')}/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MISTRAL_LOCAL_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
        
    try:
        # 300 second timeout to allow sufficient inference/loading time for local 24B model
        response = requests.post(url, json=payload, headers=headers, timeout=300)
        if response.status_code == 200:
            res_json = response.json()
            choices = res_json.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
            return None
        else:
            print(f"Mistral LLM server returned error code {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"Error connecting to Mistral LLM server at {MISTRAL_LOCAL_URL}: {e}")
        return None
