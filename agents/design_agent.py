from utils.prompts import DESIGN_AGENT_PROMPT_0
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

    def generate_design(self, ui_tech: str, backend_tech: str, db_tech: str, requirements: list, budget: str, duration: str, selected_rag: str = "", selected_guardrail: str = "", selected_action_engine: str = "", case_study_text: str = "") -> dict:
        """
        Runs ToT architecture generation.
        1. Explores candidate topologies.
        2. Evaluates constraints and tradeoffs.
        3. Consolidates the final architecture design.
        """
        tot_prompt = DESIGN_AGENT_PROMPT_0
        
        chain = tot_prompt | self.llm_json
        
        default_pillars = [
            {"title": "Agentic Orchestrator Engine", "desc": "Implement a multi-agent orchestrator utilizing ReAct patterns to parse proposals asynchronously. This ensures each step is handled efficiently, reducing manual intervention."},
            {"title": "Responsive Web Dashboard", "desc": f"Deliver an intuitive dashboard built with {ui_tech}, offering real-time progress steps and inline document editing. The interface is highly responsive and user-friendly for stakeholders."},
            {"title": "Deterministic Presentation Engine", "desc": f"Compile agent decisions into a clean JSON IR, and render a pixel-perfect PPTX deck using {backend_tech}. This automated generation eliminates human error in formatting."}
        ]
        default_architecture = [
            {"name": "Presentation layer (UI Client)", "components": [f"{ui_tech} SPA", "State Management", "Axios Client"]},
            {"name": "Application Logic (API Backend)", "components": [f"{backend_tech} Web Service", "Agent Control Loop", "Auth Middleware"]},
            {"name": "Data Integration & Cache Layer", "components": [f"{db_tech} Database", "python-pptx Builder", "Semantic RAG Store"]}
        ]
        default_business_summary = "This project is being implemented to address critical operational bottlenecks and modernize our technological infrastructure, ensuring we remain competitive in a rapidly evolving market.\\n\\nThis proposal outlines a state-of-the-art solution designed to address these requirements by leveraging modern cloud and AI capabilities. Implementing this solution will drive significant business benefits, including reduced time-to-market, maximized operational efficiency, and a strong foundation for future scalable growth."
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
            {
                "project_name": "Autonomous Deal Assistant",
                "client_industry": "Financial Services Client",
                "business_problem": [
                    "Different systems were used to store business modules.",
                    "Quality check across different systems were inconsistent.",
                    "No single source of truth for proposal templates."
                ],
                "our_approach": [
                    "Migrated legacy templates to a central knowledge repository.",
                    "Designed automatic quality checks and guardrails.",
                    "Built an agentic workflow for bid generation."
                ],
                "tech_architecture_mermaid": "graph LR\n    S[Sources] --> A[API]\n    A --> DB[(PostgreSQL)]\n    A --> V[(Qdrant)]",
                "tech_architecture_explanation": [
                    "RFP documents ingested securely.",
                    "Agents query Qdrant and compile sections.",
                    "PowerPoint generation engine creates deliverable."
                ],
                "key_technologies": [
                    "React",
                    "Flask",
                    "Qdrant",
                    "python-pptx"
                ],
                "benefits_outcome": [
                    "Reduced proposal generation time by 40%.",
                    "Ensured 100% compliance with corporate guidelines.",
                    "Enabled presales scaling to 5x more bids."
                ]
            },
            {
                "project_name": "Compliance RAG Engine",
                "client_industry": "Healthcare Provider",
                "business_problem": [
                    "Manual compliance checking was slow and error-prone.",
                    "Highly sensitive patient data required strict governance.",
                    "Frequent regulatory updates caused mapping challenges."
                ],
                "our_approach": [
                    "Implemented semantic search on policy documents.",
                    "Added LLM guardrails for healthcare compliance.",
                    "Integrated real-time auditing and logging."
                ],
                "tech_architecture_mermaid": "graph LR\n    D[Docs] --> I[Parser]\n    I --> Ch[ChromaDB]\n    Ch --> Q[Query]",
                "tech_architecture_explanation": [
                    "Healthcare policies ingested and chunked.",
                    "ChromaDB stores embeddings with semantic metadata.",
                    "Audit dashboard exposes validation logs."
                ],
                "key_technologies": [
                    "ChromaDB",
                    "LangChain",
                    "Docker",
                    "FastAPI"
                ],
                "benefits_outcome": [
                    "Automated security mapping for 10,000+ documents.",
                    "Reduced audit cycle duration by 60%.",
                    "Achieved 100% compliance audit readiness."
                ]
            }
        ]
        default_complex_diagrams = [
            {
                "title": "Reference Architecture",
                "mermaid_code": (
                    "graph LR\n"
                    "    subgraph External [External Data Sources]\n"
                    "        E1[Website Clickstream]\n"
                    "        E2[Salesforce CRM]\n"
                    "        E3[Partner Data Assets]\n"
                    "    end\n"
                    "    subgraph Internal [Internal Data Sources]\n"
                    "        I1[SAP ERP]\n"
                    "        I2[Secondary Sales DB]\n"
                    "        I3[Inhouse Applications]\n"
                    "    end\n"
                    "    subgraph Cloud [Cloud Platform]\n"
                    "        subgraph Ingestion [Data Ingestion & Orchestration]\n"
                    "            ADF(Azure Data Factory)\n"
                    "            Batch[Batch Compute]\n"
                    "        end\n"
                    "        subgraph Raw [Raw Data Zone]\n"
                    "            R1[(Raw DB)] --> R2[(Intermediate Storage)]\n"
                    "        end\n"
                    "        subgraph Curated [Curated Zone]\n"
                    "            C1[(Curated Object Storage)]\n"
                    "        end\n"
                    "        subgraph DM [Datamarts]\n"
                    "            DM1[(DM-1)]\n"
                    "            DM2[(DM-2)]\n"
                    "            DM3[(DM-3)]\n"
                    "        end\n"
                    "        Ingestion --> Raw\n"
                    "        Raw --> Curated\n"
                    "        Curated --> DM\n"
                    "    end\n"
                    "    subgraph UseCases [Use Cases]\n"
                    "        U1[Cloud API]\n"
                    "        U2[Advanced Analytics]\n"
                    "        U3[Business Intelligence]\n"
                    "    end\n"
                    "    External --> Ingestion\n"
                    "    Internal --> Ingestion\n"
                    "    DM --> UseCases"
                )
            },
            {
                "title": "Cloud Architecture",
                "mermaid_code": (
                    "graph LR\n"
                    "    subgraph Sources [Ingestion Inputs]\n"
                    "        S1[React Web App]\n"
                    "        S2[3rd Party External APIs]\n"
                    "        S3[Azure Event Grid]\n"
                    "    end\n"
                    "    subgraph Integration [Daily ETL Pipelines]\n"
                    "        ADF(Azure Data Factory)\n"
                    "        Func[Azure Functions]\n"
                    "        Entra[Microsoft Entra ID]\n"
                    "    end\n"
                    "    subgraph Storage [Data Platform Layers]\n"
                    "        Raw[(Blob Raw Container)]\n"
                    "        SQL[(Azure SQL / Cosmos)]\n"
                    "        Synapse[(Azure Synapse Analytics)]\n"
                    "    end\n"
                    "    subgraph Consumption [Reporting & DevOps]\n"
                    "        Tableau[Tableau Desktop / Cloud]\n"
                    "        DevOps[Azure DevOps & GitHub Actions]\n"
                    "    end\n"
                    "    Sources --> ADF\n"
                    "    ADF --> Raw\n"
                    "    Raw --> SQL\n"
                    "    SQL --> Synapse\n"
                    "    Synapse --> Tableau"
                )
            }
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
                "duration": duration,
                "case_study_text": case_study_text or "No case study documents provided."
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
                "similar_projects": design_data.get("similar_projects", default_similar_projects)
            }
        except Exception as e:
            print(f"Error in Solution Design Agent: {e}")
            return {
                "business_summary": default_business_summary,
                "solution_pillars": default_pillars,
                "data_flow": default_data_flow,
                "architecture": default_architecture,
                "infrastructure_approximation": default_infrastructure,
                "similar_projects": default_similar_projects
            }
