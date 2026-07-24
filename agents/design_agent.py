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

    def generate_design(self, ui_tech: str, backend_tech: str, db_tech: str, requirements: list, budget: str, duration: str, selected_rag: str = "", selected_guardrail: str = "", selected_action_engine: str = "") -> dict:
        """
        Runs ToT architecture generation.
        1. Explores candidate topologies.
        2. Evaluates constraints and tradeoffs.
        3. Consolidates the final architecture design.
        """
        tot_prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are a Principal Enterprise Solutions Architect. Act as an automated bid lifecycle expert "
                "and generate a complete, structured JSON response for a complex Enterprise IT/AI Solution Proposal RFP.\n\n"
                "You use the Tree-of-Thoughts (ToT) method to evaluate alternative architecture design paths before producing a recommendation.\n\n"
                "You are designing a system with:\n"
                "- Frontend / UI Client: {ui_tech}\n"
                "- Backend API / logic: {backend_tech}\n"
                "- Database / Storage: {db_tech}\n"
                "- Selected RAG Strategy (if any): {selected_rag}\n"
                "- Selected Guardrails (if any): {selected_guardrail}\n"
                "- Selected Action Engine (if any): {selected_action_engine}\n"
                "The client's budget constraint is {budget} and the duration is {duration}.\n\n"
                "To perform Tree-of-Thoughts:\n"
                "1. Propose 3 candidate architectural configurations or details (e.g., Option A: Monolithic simplicity, "
                "Option B: Serverless/Microservices fan-out, Option C: Decoupled SPA with high caching).\n"
                "2. Evaluate each candidate's development cost, delivery risk, scalability, and alignment with the timeline.\n"
                "3. Choose the best, most compliant option, and render it into the final output format.\n\n"
                "Your response must ONLY be a JSON object with these keys:\n"
                "- 'business_summary': a highly detailed and convenient 3-paragraph string summarizing the proposed solution, clearly articulating strategic and operational benefits.\n"
                "- 'solution_pillars': a list of exactly 3 objects, each with 'title' (short name) and 'desc' (sentence detail).\n"
                "- 'data_flow': a list of exactly 4 strings representing the high-level data flow steps.\n"
                "- 'architecture': a list of exactly 3 layers (e.g. 'Presentation layer (UI Client)', "
                "'Application Logic (API Backend)', 'Data Integration & Cache Layer') where each layer object contains "
                "'name' (string) and 'components' (list of strings representing systems/frameworks).\n"
                "- 'infrastructure_approximation': a list of exactly 5 objects representing an Azure Cost Calculator estimate. Each object has 'component' (Azure service name), 'spec', and 'estimated_monthly_cost'.\n"
                "- 'similar_projects': a list of exactly 2 objects, each with 'client_industry', 'project_name', and 'outcome'.\n"
                "- 'complex_diagrams': a list of exactly 2 complex architecture diagram objects (e.g. Reference Architecture, Cloud Architecture). Each object must have a 'title' string, and a 'columns' list. Each column has 'name', 'width_ratio' (float), and a 'zones' list. Each zone has 'name', optional 'bg_color' (e.g., 'light_green', 'light_blue', 'light_grey', 'white'), and an 'items' list. Each item has 'name' and 'shape' (must be one of: 'box', 'database', 'cloud').\n\n"
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
        default_business_summary = "This proposal outlines a state-of-the-art solution designed to address your key requirements by leveraging modern cloud and AI capabilities.\n\nOur approach ensures scalability, security, and rapid time-to-market, minimizing risks while maximizing operational efficiency."
        default_data_flow = [
            "1. User securely inputs requirements via React Dashboard.",
            "2. Orchestrator triggers Python agents to analyze and query Vector DB.",
            "3. RAG results are synthesized and stored in the core relational database.",
            "4. PPTX Generator renders the final proposal for download."
        ]
        default_infrastructure = [
            {"component": "Application Server", "spec": "8 vCPU, 32GB RAM", "estimated_monthly_cost": "$250"},
            {"component": "Relational Database", "spec": "Managed PostgreSQL, 100GB", "estimated_monthly_cost": "$150"},
            {"component": "Vector Database", "spec": "Managed Qdrant Cluster", "estimated_monthly_cost": "$200"}
        ]
        default_similar_projects = [
            {"client_industry": "Financial Services", "project_name": "Autonomous Deal Assistant", "outcome": "Reduced proposal generation time by 40%."},
            {"client_industry": "Healthcare", "project_name": "Compliance RAG Engine", "outcome": "Automated security mapping for 10,00+ documents."}
        ]
        
        try:
            res = chain.invoke({
                "ui_tech": ui_tech,
                "backend_tech": backend_tech,
                "db_tech": db_tech,
                "selected_rag": selected_rag or "None selected",
                "selected_guardrail": selected_guardrail or "None selected",
                "selected_action_engine": selected_action_engine or "None selected",
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
                "business_summary": design_data.get("business_summary", default_business_summary),
                "solution_pillars": pillars,
                "data_flow": design_data.get("data_flow", default_data_flow),
                "architecture": arch,
                "infrastructure_approximation": design_data.get("infrastructure_approximation", default_infrastructure),
                "similar_projects": design_data.get("similar_projects", default_similar_projects),
                "complex_diagrams": design_data.get("complex_diagrams", [])
            }
        except Exception as e:
            print(f"Error in Solution Design Agent: {e}")
            return {
                "business_summary": default_business_summary,
                "solution_pillars": default_pillars,
                "data_flow": default_data_flow,
                "architecture": default_architecture,
                "infrastructure_approximation": default_infrastructure,
                "similar_projects": default_similar_projects,
                "complex_diagrams": []
            }
