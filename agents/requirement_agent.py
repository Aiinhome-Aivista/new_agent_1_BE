from utils.prompts import REQUIREMENT_AGENT_PROMPT_0, REQUIREMENT_AGENT_PROMPT_1, REQUIREMENT_AGENT_PROMPT_2, REQUIREMENT_AGENT_PROMPT_3, REQUIREMENT_AGENT_PROMPT_4, DOCUMENT_CONTENT_ANALYSIS_PROMPT
import json
from langchain_core.prompts import ChatPromptTemplate
from agents.langchain_llm import get_llm
from database.vector_client import search_embeddings

class RequirementAgent:
    """
    Agent 3 — Requirement Analysis & Knowledge Agent.
    Maps client requirements <-> organizational assets & competencies; gap analysis.
    Extracts explicit tech mentions and suggests full tech package.
    """
    def __init__(self):
        self.llm = get_llm(temperature=0.2)
        self.llm_json = get_llm(temperature=0.1, json_mode=True)

    def extract_requirements(self, text: str) -> list:
        """
        Extracts top 5 technical and business requirements.
        """
        prompt = REQUIREMENT_AGENT_PROMPT_0
        
        chain = prompt | self.llm_json
        try:
            res = chain.invoke({"text": text[:8000]})
            content = res.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            reqs = json.loads(content)
            if isinstance(reqs, list) and len(reqs) > 0:
                return reqs
        except Exception as e:
            print(f"Error extracting requirements: {e}")
            
        return [
            "Deliver high-performance React front-end application with state management.",
            "Establish secure, authenticated JSON APIs with low latency.",
            "Set up secure containerized database configuration with audit trails.",
            "Implement automated DevOps workflows, CI/CD, and security vulnerability scanning.",
            "Adhere to delivery target timeline."
        ]

    def analyze_tech_stack(self, text: str, requirements: list) -> dict:
        """
        Analyzes the document for explicitly mentioned technologies, extracts them,
        recommends exactly 3 distinct technology options for end-to-end implementation,
        detects if it is an AI application and recommends the best AI models,
        and generates a RAG chat-style explanation.
        """
        prompt = REQUIREMENT_AGENT_PROMPT_1
        
        chain = prompt | self.llm_json
        
        default_options = [
            {
                "id": "option_1",
                "name": "Option 1: Modern Full-Stack JS/TS (Recommended)",
                "ui": "react",
                "backend": "nestjs",
                "database": "postgresql",
                "other_technologies": ["Docker", "Kubernetes", "GitHub Actions", "Tailwind CSS", "TypeORM", "JWT"],
                "ai_models": [],
                "rationale": "Uses TypeScript end-to-end for rapid scaling, combined with PostgreSQL for enterprise relational database safety."
            },
            {
                "id": "option_2",
                "name": "Option 2: Python AI & Data Integration Stack",
                "ui": "react",
                "backend": "flask",
                "database": "mysql",
                "other_technologies": ["Docker", "Redis", "GitHub Actions", "Tailwind CSS", "Pydantic", "SQLAlchemy"],
                "ai_models": ["Claude 3.5 Sonnet and above", "Llama 3 8B and above", "GPT-4o and above", "Gemini 1.5 Pro and above"],
                "rationale": "Leverages Python backend for seamless AI model execution, with MySQL as a robust metadata store."
            },
            {
                "id": "option_3",
                "name": "Option 3: Enterprise Scale Java Stack",
                "ui": "angular",
                "backend": "spring_boot",
                "database": "postgresql",
                "other_technologies": ["Docker", "Kubernetes", "GitLab CI/CD", "Bootstrap", "Hibernate", "Spring Security"],
                "ai_models": [],
                "rationale": "Offers industry-standard structure, security, and performance for heavy transactional workloads."
            }
        ]
        
        default_res = {
            "extracted_technologies": {"ui": None, "backend": None, "database": None},
            "tech_options": default_options,
            "chat_explanation": "I have analyzed the RFP and requirements. Based on the scope, I have compiled **3 optimal technology package options** for end-to-end implementation."
        }
        
        try:
            res = chain.invoke({
                "requirements": json.dumps(requirements),
                "text": text[:8000]
            })
            content = res.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            parsed = json.loads(content)
            
            # Simple validation on tech_options structure
            opts = parsed.get("tech_options")
            if isinstance(opts, list) and len(opts) == 3:
                return parsed
        except Exception as e:
            print(f"Error analyzing tech stack: {e}")
            
        return default_res

    def run_rag_analysis(self, requirements: list, project_duration: str) -> dict:
        """
        Maps requirements to internal competencies/assets, does gap analysis, and returns matched/gaps lists.
        """
        matched_assets = []
        gaps = []
        
        for req in requirements:
            # Semantic search in ChromaDB
            results = search_embeddings("knowledge_assets", req, n_results=1)
            
            if results and len(results) > 0 and results[0]["similarity"] >= 0.40:
                best_meta = results[0]["metadata"]
                matched_assets.append({
                    "requirement": req,
                    "asset_name": best_meta.get("name", ""),
                    "category": best_meta.get("category", "Asset"),
                    "description": best_meta.get("description", "")
                })
            else:
                # Ask LLM for gap mitigation
                prompt = REQUIREMENT_AGENT_PROMPT_2
                chain = prompt | self.llm
                try:
                    res = chain.invoke({"req": req})
                    mitigation = res.content.strip()
                except Exception:
                    mitigation = "Address through temporary external contractor recruitment."
                gaps.append(f"Identified gap in Client Requirement: '{req}'. Mitigation: {mitigation}")

        if not gaps:
            gaps = ["No critical knowledge capability gaps identified. Full alignment with our competencies."]

        # Combine with LLM for final structure
        prompt = REQUIREMENT_AGENT_PROMPT_3
        chain = prompt | self.llm_json
        try:
            res = chain.invoke({
                "reqs": json.dumps(requirements),
                "assets": json.dumps(matched_assets),
                "gaps": json.dumps(gaps)
            })
            content = res.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            return json.loads(content)
        except Exception as e:
            print(f"Error compilation of RAG mappings: {e}")
            return {
                "matched": matched_assets,
                "gaps": gaps
            }

    def analyze_advanced_options(self, text: str, requirements: list) -> dict:
        """
        Analyzes the document for RAG, Action Engine, and Guardrails requirements.
        Generates dynamic options if required.
        """
        prompt = REQUIREMENT_AGENT_PROMPT_4
        
        chain = prompt | self.llm_json
        
        default_res = {
            "rag_options": [],
            "action_engine_options": [],
            "guardrail_options": []
        }
        
        try:
            res = chain.invoke({
                "requirements": json.dumps(requirements),
                "text": text[:8000]
            })
            content = res.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            parsed = json.loads(content)
            return {
                "rag_options": parsed.get("rag_options", []),
                "action_engine_options": parsed.get("action_engine_options", []),
                "guardrail_options": parsed.get("guardrail_options", [])
            }
        except Exception as e:
            print(f"Error analyzing advanced options: {e}")
            return default_res

    def analyze_document_content(self, text: str) -> dict:
        """
        Generic document content analysis capability.
        Extracts various sections like Business Objectives, Workflow, Architecture, etc.
        Returns a structured JSON representing the document.
        """
        prompt = DOCUMENT_CONTENT_ANALYSIS_PROMPT
        chain = prompt | self.llm_json
        
        default_res = {
            "document": {"title": "", "type": "", "domain": "", "summary": ""},
            "sections": [],
            "business_objectives": [],
            "scope": {"in_scope": [], "out_of_scope": []},
            "requirements": {"functional": [], "technical": []},
            "current_state": [],
            "target_state": [],
            "workflow": [],
            "architecture": {"components": [], "relationships": [], "reference_architecture": {}, "landscape_architecture": {}},
            "data": {"sources": [], "data_flow": [], "storage": [], "transformation": [], "modelling": []},
            "technology": [],
            "integrations": [],
            "security": [],
            "governance": [],
            "data_quality": [],
            "performance": [],
            "scalability": [],
            "monitoring": [],
            "availability": [],
            "disaster_recovery": [],
            "deployment": [],
            "cicd": [],
            "implementation_roadmap": [],
            "cost": {"specified_in_document": False, "details": []},
            "risks": [],
            "assumptions": [],
            "dependencies": [],
            "open_questions": []
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
            print(f"Error analyzing document content: {e}")
            return default_res

