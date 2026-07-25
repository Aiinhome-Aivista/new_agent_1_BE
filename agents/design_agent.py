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
                "- 'solution_pillars': a list of exactly 3 objects, each with 'title' (short name) and 'desc' (a concise but informative paragraph of exactly 2 to 3 sentences and maximum 40 words explaining the pillar so the reader understands it well without overflowing the presentation slide).\n"
                "- 'data_flow': a list of exactly 4 strings representing the high-level data flow steps.\n"
                "- 'architecture': a list of exactly 3 layers (e.g. 'Presentation layer (UI Client)', "
                "'Application Logic (API Backend)', 'Data Integration & Cache Layer') where each layer object contains "
                "'name' (string) and 'components' (list of strings representing systems/frameworks).\n"
                "- 'infrastructure_approximation': a list of exactly 5 objects representing an Azure Cost Calculator estimate. Each object has 'component' (Azure service name), 'spec', and 'estimated_monthly_cost'.\n"
                "- 'similar_projects': a list of exactly 2 objects representing detailed previous project case studies. "
                "If previous case study text/documents are provided in user input, analyze and extract/summarize them to construct these case studies. "
                "If not provided, generate 2 highly relevant realistic case studies matching the client's RFP requirements. "
                "Each case study object must have these keys:\n"
                "  * 'project_name': short name of the project (e.g., 'Teradata to Snowflake migration').\n"
                "  * 'client_industry': industry/details of the client (e.g., 'Lifestyle Footwear Company in US').\n"
                "  * 'business_problem': a list of exactly 3-4 strings representing key business/technical challenges.\n"
                "  * 'our_approach': a list of exactly 3-4 strings detailing the steps or architectural choices built to solve it.\n"
                "  * 'tech_architecture_mermaid': a valid, clean Mermaid.js flowchart (starting with 'graph LR' for optimal wide layout) representing the technical architecture of that case study.\n"
                "  * 'tech_architecture_explanation': a list of exactly 3 strings representing concise summaries (1-2 sentences) of: 1. Source/Ingestion, 2. Storage/Processing, and 3. Consumption/Reporting.\n"
                "  * 'key_technologies': a list of exactly 3-4 technologies used (e.g. ['Snowflake', 'Azure Data Factory']).\n"
                "  * 'benefits_outcome': a list of exactly 3-4 strings summarizing benefits and outcomes.\n\n"
                "Do not include any explanation or markdown formatting outside the JSON."
            )),
            ("user", "Requirements:\n{requirements}\n\nBudget: {budget}\nDuration: {duration}\n\nCase Study Documents Text:\n{case_study_text}")
        ])
        
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
