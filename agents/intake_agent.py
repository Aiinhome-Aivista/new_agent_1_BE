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
        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are a document processing assistant specialized in RFPs and proposals.\n"
                "Classify the text chunk into exactly one of these labels:\n"
                "- Background\n"
                "- Requirements\n"
                "- Financial & Sizing\n"
                "- Compliance & Security\n"
                "- Other\n"
                "Respond ONLY with the selected label (e.g. 'Requirements'). No markdown, punctuation or explanation."
            )),
            ("user", "RFP Document Chunk:\n\n{chunk}")
        ])
        
        chain = prompt | self.llm
        try:
            res = chain.invoke({"chunk": chunk_content[:1500]})
            clean = res.content.strip().strip("'\"`").strip()
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
        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are an assistant that extracts metadata from client RFPs.\n"
                "Extract the following values if they are present in the text:\n"
                "1. Client Name (the company asking for the proposal, e.g. 'Acme Corporation')\n"
                "2. Project Duration/Timeline (e.g. '14 Weeks')\n"
                "3. Target Budget (e.g. '$250,000')\n"
                "Respond ONLY with a JSON object containing keys: 'client_name', 'project_duration', 'budget'.\n"
                "Do not include markdown code block syntax or comments."
            )),
            ("user", "RFP Text Snippet:\n\n{text}")
        ])
        
        chain = prompt | self.llm_json
        try:
            res = chain.invoke({"text": full_document_text[:5000]})
            content = res.content.strip()
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
