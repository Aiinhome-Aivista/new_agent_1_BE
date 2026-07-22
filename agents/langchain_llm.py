import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv(override=True)

MISTRAL_LOCAL_URL = os.getenv("MISTRAL_LOCAL_URL")
MISTRAL_LOCAL_MODEL = os.getenv("MISTRAL_LOCAL_MODEL")

if not MISTRAL_LOCAL_URL or not MISTRAL_LOCAL_MODEL:
    raise ValueError("MISTRAL_LOCAL_URL or MISTRAL_LOCAL_MODEL is not set in the .env file")

def get_llm(temperature=0.2, json_mode=False):
    """
    Returns a LangChain ChatOpenAI object configured to interact with the local Mistral LLM endpoint.
    If json_mode is True, response_format is set to JSON object.
    """
    base_url = f"{MISTRAL_LOCAL_URL.rstrip('/')}/v1"
    
    model_kwargs = {}
    if json_mode:
        model_kwargs["response_format"] = {"type": "json_object"}
        
    return ChatOpenAI(
        base_url=base_url,
        api_key="ollama",  # Dummy key required by ChatOpenAI
        model=MISTRAL_LOCAL_MODEL,
        temperature=temperature,
        model_kwargs=model_kwargs,
        timeout=300
    )
