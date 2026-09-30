from utils.prompts import LLM_CLIENT_SYS_PROMPT_0
import os
import json
import requests
import time
from dotenv import load_dotenv
from utils.token_counter import add_tokens

load_dotenv(override=True)

MODE = os.getenv("MODE", "Local")
MISTRAL_LOCAL_URL = os.getenv("MISTRAL_LOCAL_URL")
MISTRAL_LOCAL_MODEL = os.getenv("MISTRAL_LOCAL_MODEL")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "mistral-small-latest")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# Local LLM Performance Settings
LLM_STREAM = str(os.getenv("LLM_STREAM", "false")).lower() == "true"
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2048"))
LLM_NUM_CTX = int(os.getenv("LLM_NUM_CTX", "4096"))
LLM_KEEP_ALIVE = os.getenv("LLM_KEEP_ALIVE", "30m")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.15"))
LLM_TOP_P = float(os.getenv("LLM_TOP_P", "0.9"))

def query_llm(system_prompt, user_prompt, temperature=None, max_tokens=None, json_mode=False):
    """
    Sends a chat completion request to the chosen LLM endpoint.
    """
    print(f"--- Using LLM in {MODE.upper()} mode ---")
    headers = {
        "Content-Type": "application/json"
    }

    if MODE.lower() == "gemini":
        print(f"[SUCCESS] REST Client: Connecting to Gemini API (Model: {GEMINI_MODEL})")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"System: {system_prompt}\n\nUser: {user_prompt}"}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"
            
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=300)
            if response.status_code == 200:
                res_json = response.json()
                
                # Token tracking
                usage = res_json.get("usageMetadata", {})
                prompt_tokens = usage.get("promptTokenCount", 0)
                completion_tokens = usage.get("candidatesTokenCount", 0)
                total_tokens = usage.get("totalTokenCount", 0)
                add_tokens(prompt_tokens, completion_tokens, total_tokens)

                candidates = res_json.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
                return None
            else:
                print(f"Gemini API failed with status {response.status_code}: {response.text}")
                return None
        except Exception as e:
            print(f"Gemini API request exception: {e}")
            return None

    elif MODE.lower() == "cloud":
        print(f"[SUCCESS] REST Client: Connecting to Mistral Cloud API (Model: {MODEL_NAME})")
        url = "https://api.mistral.ai/v1/chat/completions"
        headers["Authorization"] = f"Bearer {MISTRAL_API_KEY}"
        payload = {
            "model": MODEL_NAME,
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
            response = requests.post(url, json=payload, headers=headers, timeout=300)
            if response.status_code == 200:
                res_json = response.json()
                
                # Token tracking
                usage = res_json.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", 0)
                add_tokens(prompt_tokens, completion_tokens, total_tokens)

                choices = res_json.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
                return None
            else:
                print(f"Mistral Cloud API failed with status {response.status_code}: {response.text}")
                return None
        except Exception as e:
            print(f"Mistral Cloud API request exception: {e}")
            return None
    
    # Use .env settings, fallback to function arguments if .env is missing/default
    final_temp = temperature if temperature is not None else LLM_TEMPERATURE
    final_max_tokens = max_tokens if max_tokens is not None else LLM_MAX_TOKENS

    print(f"[SUCCESS] REST Client: Connecting to Local Mistral (URL: {MISTRAL_LOCAL_URL}, Model: {MISTRAL_LOCAL_MODEL})")
    # Try Ollama endpoint format first for Local Mode
    url_ollama = f"{MISTRAL_LOCAL_URL.rstrip('/')}/api/chat"
    payload_ollama = {
        "model": MISTRAL_LOCAL_MODEL,
        "keep_alive": LLM_KEEP_ALIVE,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "options": {
            "temperature": final_temp,
            "top_p": LLM_TOP_P,
            "num_predict": final_max_tokens,
            "num_ctx": LLM_NUM_CTX
        },
        "stream": LLM_STREAM
    }
    
    if json_mode:
        payload_ollama["format"] = "json"
        
    try:
        start_time = time.time()
        # Enable stream parameter in requests if LLM_STREAM is true
        response = requests.post(url_ollama, json=payload_ollama, headers=headers, stream=LLM_STREAM, timeout=300)
        
        if response.status_code == 200:
            if LLM_STREAM:
                # Handle Streaming response internally to calculate latencies
                first_token_time = None
                full_content = ""
                prompt_tokens = 0
                completion_tokens = 0
                
                for line in response.iter_lines():
                    if line:
                        if first_token_time is None:
                            first_token_time = time.time()
                            first_latency = (first_token_time - start_time) * 1000
                            print(f"[LLM] First-token latency: {first_latency:.2f} ms")
                            
                        chunk = json.loads(line.decode('utf-8'))
                        if "message" in chunk and "content" in chunk["message"]:
                            full_content += chunk["message"]["content"]
                            
                        if chunk.get("done"):
                            prompt_tokens = chunk.get("prompt_eval_count", 0)
                            completion_tokens = chunk.get("eval_count", 0)
                            
                total_time = (time.time() - start_time) * 1000
                print(f"[LLM] Total response time: {total_time:.2f} ms")
                total_tokens = prompt_tokens + completion_tokens
                add_tokens(prompt_tokens, completion_tokens, total_tokens)
                return full_content
            else:
                # Synchronous response handling (if stream=false)
                res_json = response.json()
                total_time = (time.time() - start_time) * 1000
                print(f"[LLM] Total response time (No Stream): {total_time:.2f} ms")
                
                # Token tracking
                prompt_tokens = res_json.get("prompt_eval_count", 0)
                completion_tokens = res_json.get("eval_count", 0)
                total_tokens = prompt_tokens + completion_tokens
                add_tokens(prompt_tokens, completion_tokens, total_tokens)

                return res_json.get("message", {}).get("content", "")
        else:
            print(f"Ollama API failed with status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Ollama API request exception: {e}")
        pass # Fallback to OpenAI API format
        
    # Try OpenAI format for Local Mode
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
            
            # Token tracking
            usage = res_json.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)
            add_tokens(prompt_tokens, completion_tokens, total_tokens)

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

def extract_pdf_metadata(text):
    """
    Uses the LLM to analyze the extracted text from a PDF/doc in the knowledge base.
    Returns a dictionary with 'category', 'capabilities', and 'description'.
    """
    sys_prompt = LLM_CLIENT_SYS_PROMPT_0
    user_prompt = f"Document Text:\n\n{text[:4000]}"
    try:
        response = query_llm(sys_prompt, user_prompt, temperature=0.1, json_mode=True)
        if response:
            return safe_json_loads(response, {
                "category": "Asset",
                "tags": ["File Upload"],
                "description": text[:200] + "..." if len(text) > 200 else text
            })
    except Exception as e:
        print(f"Error extracting metadata from PDF: {e}")
    return {
        "category": "Asset",
        "tags": ["File Upload"],
        "description": text[:200] + "..." if len(text) > 200 else text
    }

def validate_document(extracted_text):
    """
    Validates if the extracted text of an uploaded document is relevant to the application's domain.
    Returns a tuple (is_approved, response_json).
    """
    threshold = int(os.environ.get("RELEVANCE_THRESHOLD", "80"))
    system_prompt = f"""You are an intelligent document validation assistant.
Your task is to determine whether an uploaded document is relevant to the application's domain (IT Solutions, Software Development Proposals, RFP responses, project requirements specifications, technical case studies, software architectures, and technology competency profiles) before it is stored in the knowledge base.

Instructions:
1. Compare the document with the expected domain/context of the application.
2. IMPORTANT rules for scoring:
   - The document must be an organizational asset (such as an RFP, corporate proposal, business case study, technical architecture, or capability overview).
   - EXCLUDE personal resumes, CVs (Curriculum Vitae), career history, portfolios, cover letters, and individual bio profiles. Even if they list IT technologies or software engineering skills, they are NOT relevant to the proposal creation or knowledge base domain and MUST be REJECTED (relevance_score must be below {threshold}, ideally 0-40%).
   - EXCLUDE any non-IT documents (e.g. recipes, non-IT articles, news, fiction, general blogs).
3. Calculate a relevance score between 0 and 100%. Be conservative and strict.
4. The minimum acceptance threshold is: {threshold}

Decision Rules:
- If relevance_score >= {threshold}:
    status = "APPROVED"
- If relevance_score < {threshold}:
    status = "REJECTED"

Return your response strictly in the following JSON format:
{{
  "status": "APPROVED" or "REJECTED",
  "relevance_score": <integer score>,
  "threshold": {threshold},
  "reason": "Brief explanation of why the document is or is not relevant, explicitly mentioning if it is a personal CV/resume.",
  "matched_topics": ["Topic 1", "Topic 2"],
  "missing_topics": ["Topic A", "Topic B"]
}}
"""
    user_prompt = f"Document content:\n\n{extracted_text[:6000]}"
    res_str = query_llm(system_prompt, user_prompt, temperature=0.1, json_mode=True)
    res_json = safe_json_loads(res_str, None)
    
    if not res_json:
        res_json = {
            "status": "REJECTED",
            "relevance_score": 0,
            "threshold": threshold,
            "reason": "Failed to parse validation response from LLM.",
            "matched_topics": [],
            "missing_topics": []
        }
        
    status_decision = res_json.get("status", "REJECTED")
    relevance_score = res_json.get("relevance_score", 0)
    
    if relevance_score < threshold:
        status_decision = "REJECTED"
        res_json["status"] = "REJECTED"
        
    return (status_decision == "APPROVED", res_json)


