import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv(override=True)

MISTRAL_MODE = os.getenv("MISTRAL_MODE", "Local")
MISTRAL_LOCAL_URL = os.getenv("MISTRAL_LOCAL_URL")
MISTRAL_LOCAL_MODEL = os.getenv("MISTRAL_LOCAL_MODEL")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "mistral-small-latest")


def get_llm(temperature=0.2, json_mode=False):
    """
    Returns a LangChain ChatOpenAI object configured to interact with the chosen Mistral LLM endpoint.
    If json_mode is True, response_format is set to JSON object.
    """
    print(f"--- Using Mistral LLM in {MISTRAL_MODE.upper()} mode via LangChain ---")
    model_kwargs = {}
    if json_mode:
        model_kwargs["response_format"] = {"type": "json_object"}

    if MISTRAL_MODE.lower() == "cloud":
        if not MISTRAL_API_KEY:
            raise ValueError("MISTRAL_API_KEY is not set in the .env file")
        return ChatOpenAI(
            base_url="https://api.mistral.ai/v1",
            api_key=MISTRAL_API_KEY,
            model=MODEL_NAME,
            temperature=temperature,
            model_kwargs=model_kwargs,
            timeout=300
        )
    else:
        if not MISTRAL_LOCAL_URL or not MISTRAL_LOCAL_MODEL:
            raise ValueError("MISTRAL_LOCAL_URL or MISTRAL_LOCAL_MODEL is not set in the .env file")
        base_url = f"{MISTRAL_LOCAL_URL.rstrip('/')}/v1"
        return ChatOpenAI(
            base_url=base_url,
            api_key="ollama",  # Dummy key required by ChatOpenAI
            model=MISTRAL_LOCAL_MODEL,
            temperature=temperature,
            model_kwargs=model_kwargs,
            timeout=300
        )
