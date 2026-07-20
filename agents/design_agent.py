import json
from langchain_core.prompts import ChatPromptTemplate
from agents.langchain_llm import get_llm

class DesignAgent:
    """
    Agent 4 — Solution Design Agent.
    Generates solution approach + landscape architecture.
    Uses Tree-of-Thoughts (ToT) reasoning (multiple architectural candidates compared).
    """
    def __init__(self):
        self.llm = get_llm(temperature=0.3)
        self.llm_json = get_llm(temperature=0.2, json_mode=True)

    def generate_design(self, ui_tech: str, backend_tech: str, db_tech: str, requirements: list, budget: str, duration: str) -> dict:
        """
        Runs ToT architecture generation.
        1. Explores candidate topologies.
        2. Evaluates constraints and tradeoffs.
        3. Consolidates the final architecture design.
        """
        tot_prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are a Chief Systems Architect. You use the Tree-of-Thoughts (ToT) method "
                "to evaluate alternative architecture design paths before producing a recommendation.\n\n"
                "You are designing a system with:\n"
                "- Frontend / UI Client: {ui_tech}\n"
                "- Backend API / logic: {backend_tech}\n"
                "- Database / Storage: {db_tech}\n"
                "The client's budget constraint is {budget} and the duration is {duration}.\n\n"
                "To perform Tree-of-Thoughts:\n"
                "1. Propose 3 candidate architectural configurations or details (e.g., Option A: Monolithic simplicity, "
                "Option B: Serverless/Microservices fan-out, Option C: Decoupled SPA with high caching).\n"
                "2. Evaluate each candidate's development cost, delivery risk, scalability, and alignment with the timeline.\n"
                "3. Choose the best, most compliant option, and render it into the final output format.\n\n"
                "Your response must ONLY be a JSON object with these two keys:\n"
                "- 'solution_pillars': a list of exactly 3 objects, each with 'title' (short name) and 'desc' (sentence detail).\n"
                "- 'architecture': a list of exactly 3 layers (e.g. 'Presentation layer (UI Client)', "
                "'Application Logic (API Backend)', 'Data Integration & Cache Layer') where each layer object contains "
                "'name' (string) and 'components' (list of strings representing systems/frameworks).\n\n"
                "Do not include any explanation or markdown formatting outside the JSON."
            )),
            ("user", "Requirements:\n{requirements}\n\nBudget: {budget}\nDuration: {duration}")
        ])
        
        chain = tot_prompt | self.llm_json
        
        default_pillars = [
            {"title": "Agentic Orchestrator Engine", "desc": "Implement a stateful multi-agent orchestrator utilizing ReAct patterns to parse proposals asynchronously."},
            {"title": "Responsive Web Dashboard", "desc": f"Deliver an intuitive dashboard built with {ui_tech}, offering real-time progress steps and inline document editing."},
            {"title": "Deterministic Presentation Engine", "desc": f"Compile agent decisions into a clean JSON IR, and render a pixel-perfect PPTX deck using {backend_tech}."}
        ]
        default_architecture = [
            {"name": "Presentation layer (UI Client)", "components": [f"{ui_tech} SPA", "State Management", "Axios Client"]},
            {"name": "Application Logic (API Backend)", "components": [f"{backend_tech} Web Service", "Agent Control Loop", "Auth Middleware"]},
            {"name": "Data Integration & Cache Layer", "components": [f"{db_tech} Database", "python-pptx Builder", "Semantic RAG Store"]}
        ]
        
        try:
            res = chain.invoke({
                "ui_tech": ui_tech,
                "backend_tech": backend_tech,
                "db_tech": db_tech,
                "requirements": json.dumps(requirements),
                "budget": budget,
                "duration": duration
            })
            content = res.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            design_data = json.loads(content)
            
            # Basic validation
            pillars = design_data.get("solution_pillars", default_pillars)
            arch = design_data.get("architecture", default_architecture)
            
            return {
                "solution_pillars": pillars,
                "architecture": arch
            }
        except Exception as e:
            print(f"Error in Solution Design Agent: {e}")
            return {
                "solution_pillars": default_pillars,
                "architecture": default_architecture
            }
