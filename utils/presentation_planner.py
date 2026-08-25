import json
from agents.langchain_llm import get_llm
from langchain_core.prompts import ChatPromptTemplate

PRESENTATION_PLANNER_PROMPT = ChatPromptTemplate.from_messages([
            ("system", (
                "You are an expert Presentation Planner.\n"
                "Based on the Document Understanding metadata and Content Analysis data, decide which dynamic document-specific slides should be included in the presentation.\n"
                "The dynamic slides should logically flow from the document's content (e.g. Executive Summary, Functional Flow, Architecture, Security, etc.).\n"
                "DO NOT include these mandatory slides in your response (they are added automatically): Technology, Cost, Reference Architecture, Landscape Architecture, Thank You, Effort & Person-Hour Conversion, Skills Inventory & Competency Mapping.\n\n"
                "Respond ONLY with a JSON object containing a 'slides' key, which is a list of objects. Each object must have a 'type' (slug) and 'title' (display title).\n"
                "Example:\n"
                "{\n"
                "  \"slides\": [\n"
                "    {\"type\": \"executive_summary\", \"title\": \"Executive Summary\"},\n"
                "    {\"type\": \"multi_agent_architecture\", \"title\": \"Multi-Agent Architecture\"}\n"
                "  ]\n"
                "}\n"
                "Do not include any explanation or markdown formatting outside the JSON."
            )),
            ("user", "Document Understanding:\n{doc_understanding}\n\nContent Analysis:\n{content_analysis}")
        ])

class PresentationPlanner:
    def __init__(self):
        self.llm_json = get_llm(temperature=0.1, json_mode=True)
        
        self.mandatory_slides = [
            {"type": "technology", "title": "Technology Stack"},
            {"type": "cost", "title": "Cost Estimation"},
            {"type": "reference_architecture", "title": "Reference Architecture"},
            {"type": "landscape_architecture", "title": "Landscape Architecture"},
            {"type": "effort_and_person_hour", "title": "Effort & Person-Hour Conversion"},
            {"type": "skills_mapping", "title": "Skills Inventory & Competency Mapping"},
            {"type": "thank_you", "title": "Thank You"}
        ]

    def plan_presentation(self, doc_understanding: dict, content_analysis: dict) -> dict:
        """
        Receives Document Understanding and Content Analysis outputs.
        Generates a structured presentation plan (dynamic slides + mandatory slides).
        """
        prompt = PRESENTATION_PLANNER_PROMPT
        chain = prompt | self.llm_json
        
        try:
            res = chain.invoke({
                "doc_understanding": json.dumps(doc_understanding),
                "content_analysis": json.dumps(content_analysis)
            })
            content = res.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            parsed = json.loads(content)
            dynamic_slides = parsed.get("slides", [])
        except Exception as e:
            print(f"Error in PresentationPlanner: {e}")
            dynamic_slides = [
                {"type": "executive_summary", "title": "Executive Summary"}
            ]
            
        # Build Presentation IR
        presentation_ir = {
            "metadata": {
                "title": doc_understanding.get("title", "Presentation"),
                "document_type": doc_understanding.get("document_type", "Unknown"),
                "domain": doc_understanding.get("domain", "Unknown")
            },
            "dynamic_slides": dynamic_slides,
            "mandatory_slides": {
                slide["type"]: {} for slide in self.mandatory_slides
            },
            "slide_plan": dynamic_slides + self.mandatory_slides
        }
        
        return presentation_ir
