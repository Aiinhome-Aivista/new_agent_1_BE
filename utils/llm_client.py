import os
import json
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

MISTRAL_LOCAL_URL = os.getenv("MISTRAL_LOCAL_URL")
MISTRAL_LOCAL_MODEL = os.getenv("MISTRAL_LOCAL_MODEL")

if not MISTRAL_LOCAL_URL or not MISTRAL_LOCAL_MODEL:
    raise ValueError("MISTRAL_LOCAL_URL or MISTRAL_LOCAL_MODEL is not set in the .env file")

def query_llm(system_prompt, user_prompt, temperature=0.2, max_tokens=2048, json_mode=False):
    """
    Sends a chat completion request to the local Mistral LLM endpoint.
    If the endpoint is down, it returns None, enabling the orchestrator to fall back to static/heuristic mocks.
    """
    headers = {
        "Content-Type": "application/json"
    }
    
    # Try Ollama endpoint format first
    url_ollama = f"{MISTRAL_LOCAL_URL.rstrip('/')}/api/chat"
    payload_ollama = {
        "model": MISTRAL_LOCAL_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens
        },
        "stream": False
    }
    
    if json_mode:
        payload_ollama["format"] = "json"
        
    try:
        response = requests.post(url_ollama, json=payload_ollama, headers=headers, timeout=300)
        if response.status_code == 200:
            res_json = response.json()
            return res_json.get("message", {}).get("content", "")
        else:
            print(f"Ollama API failed with status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Ollama API request exception: {e}")
        pass # Fallback to OpenAI API format
        
    # Try OpenAI format
    url_openai = f"{MISTRAL_LOCAL_URL.rstrip('/')}/v1/chat/completions"
    payload_openai = {
        "model": MISTRAL_LOCAL_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    if json_mode:
        payload_openai["response_format"] = {"type": "json_object"}
        
    try:
        response = requests.post(url_openai, json=payload_openai, headers=headers, timeout=300)
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

def safe_json_loads(json_str, fallback):
    """
    Safely parses JSON string, removing any markdown code blocks if present.
    Returns fallback if parsing fails.
    """
    if not json_str:
        return fallback
    try:
        # Sometimes LLMs wrap json in markdown blocks like ```json ... ```
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()
        return json.loads(json_str)
    except Exception as e:
        print(f"JSON parsing error: {e}")
        return fallback
