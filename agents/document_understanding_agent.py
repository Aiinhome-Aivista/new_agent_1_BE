import json
from agents.langchain_llm import get_llm
from utils.prompts import DOCUMENT_UNDERSTANDING_PROMPT

class DocumentUnderstandingAgent:
    """
    Agent responsible for analyzing generic technical documents, identifying their type,
    and extracting high-level metadata (domain, presence of architecture, security, etc.)
    """
    def __init__(self):
        self.llm_json = get_llm(temperature=0.1, json_mode=True)

    def understand_document(self, text: str) -> dict:
        """
        Identifies the document type and extracts high-level metadata.
        """
        prompt = DOCUMENT_UNDERSTANDING_PROMPT
        chain = prompt | self.llm_json
        
        default_res = {
            "document_type": "Unknown",
            "title": "Untitled Document",
            "domain": "Unknown",
            "summary": "Could not extract summary.",
            "sections_present": [],
            "has_architecture": False,
            "has_workflow": False,
            "has_security": False,
            "has_technology": False,
            "has_cost": False,
            "has_implementation_plan": False,
            "has_rag": False,
            "cloud_provider": "Not Specified"
        }
        
        try:
            res = chain.invoke({"text": text[:12000]})
            content = res.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            parsed = json.loads(content)
            return parsed
        except Exception as e:
            print(f"Error in DocumentUnderstandingAgent: {e}")
            return default_res
