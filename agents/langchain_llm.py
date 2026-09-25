import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.callbacks import BaseCallbackHandler
from utils.token_counter import add_tokens

load_dotenv(override=True)

MODE = os.getenv("MODE", "Local")
MISTRAL_LOCAL_URL = os.getenv("MISTRAL_LOCAL_URL")
MISTRAL_LOCAL_MODEL = os.getenv("MISTRAL_LOCAL_MODEL")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "mistral-small-latest")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

class TokenUsageCallbackHandler(BaseCallbackHandler):
    def on_llm_end(self, response, **kwargs):
        if response.llm_output is not None:
            token_usage = response.llm_output.get("token_usage", {})
            prompt_tokens = token_usage.get("prompt_tokens", 0)
            completion_tokens = token_usage.get("completion_tokens", 0)
            total_tokens = token_usage.get("total_tokens", 0)
            
            # Print it
            add_tokens(prompt_tokens, completion_tokens, total_tokens)

def get_llm(temperature=0.2, json_mode=False):
    """
    Returns a LangChain Chat object configured to interact with the chosen LLM endpoint.
    If json_mode is True, response_format is set to JSON object (if supported).
    """
    print(f"--- Using LLM in {MODE.upper()} mode via LangChain ---")
    model_kwargs = {}
    if json_mode:
        model_kwargs["response_format"] = {"type": "json_object"}

    callbacks = [TokenUsageCallbackHandler()]

    if MODE.lower() == "gemini":
        print(f"[SUCCESS] LangChain: Connecting to Gemini API (Model: {GEMINI_MODEL})")
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in the .env file")
        # json_mode via model_kwargs might not be natively supported by ChatGoogleGenerativeAI in all versions,
        # but passing it usually works or is ignored safely.
        return ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GEMINI_API_KEY,
            temperature=temperature,
            model_kwargs=model_kwargs,
            callbacks=callbacks
        )
    elif MODE.lower() == "cloud":
        print(f"[SUCCESS] LangChain: Connecting to Mistral Cloud API (Model: {MODEL_NAME})")
        if not MISTRAL_API_KEY:
            raise ValueError("MISTRAL_API_KEY is not set in the .env file")
        return ChatOpenAI(
            base_url="https://api.mistral.ai/v1",
            api_key=MISTRAL_API_KEY,
            model=MODEL_NAME,
            temperature=temperature,
            model_kwargs=model_kwargs,
            timeout=300,
            callbacks=callbacks
        )
    else:
        print(f"[SUCCESS] LangChain: Connecting to Local Mistral (URL: {MISTRAL_LOCAL_URL}, Model: {MISTRAL_LOCAL_MODEL})")
        if not MISTRAL_LOCAL_URL or not MISTRAL_LOCAL_MODEL:
            raise ValueError("MISTRAL_LOCAL_URL or MISTRAL_LOCAL_MODEL is not set in the .env file")
        base_url = f"{MISTRAL_LOCAL_URL.rstrip('/')}/v1"
        return ChatOpenAI(
            base_url=base_url,
            api_key="ollama",  # Dummy key required by ChatOpenAI
            model=MISTRAL_LOCAL_MODEL,
            temperature=temperature,
            model_kwargs=model_kwargs,
            timeout=300,
            callbacks=callbacks
        )
