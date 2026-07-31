from utils.prompts import INTAKE_AGENT_PROMPT_0, INTAKE_AGENT_PROMPT_1
import json
from langchain_core.prompts import ChatPromptTemplate
from agents.langchain_llm import get_llm

class IntakeAgent:
    """
    Agent 2 — Document Intake & Processing Agent.
    Ingests, parses, classifies & chunks RFP/competency/asset/financial docs.
    """
    def __init__(self):
        self.llm = get_llm(temperature=0.0)
        self.llm_json = get_llm(temperature=0.0, json_mode=True)

    def classify_chunk(self, chunk_content: str) -> str:
        """
        Classifies RFP chunk content into pre-defined categories.
        """
        prompt = INTAKE_AGENT_PROMPT_0
        
        chain = prompt | self.llm
        try:
            res = chain.invoke({"chunk": chunk_content[:1500]})
            content_str = res.content
            if isinstance(content_str, list):
                content_str = content_str[0].get("text", "") if len(content_str) > 0 and isinstance(content_str[0], dict) else str(content_str)
            clean = content_str.strip().strip("'\"`").strip()
            for cat in ["Background", "Requirements", "Financial & Sizing", "Compliance & Security", "Other"]:
                if cat.lower() in clean.lower():
                    return cat
        except Exception as e:
            print(f"Error classifying chunk: {e}")
        return "Other"

    def extract_metadata(self, full_document_text: str) -> dict:
        """
        Extracts client name, project duration, and budget from RFP text.
        """
        prompt = INTAKE_AGENT_PROMPT_1
        
        chain = prompt | self.llm_json
        try:
            res = chain.invoke({"text": full_document_text[:5000]})
            content_str = res.content
            if isinstance(content_str, list):
                content_str = content_str[0].get("text", "") if len(content_str) > 0 and isinstance(content_str[0], dict) else str(content_str)
            content = content_str.strip()
            # Clean markdown code blocks if the model accidentally returned them
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            return json.loads(content)
        except Exception as e:
            print(f"Error extracting metadata: {e}")
            return {}
