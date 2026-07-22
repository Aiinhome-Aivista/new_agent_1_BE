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
        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are a pre-sales engineering assistant.\n"
                "Given the client document text, extract the top 5 technical and business requirements for this solution.\n"
                "Respond ONLY as a JSON list of strings, with no other text, comments or markdown blocks.\n"
                "Example format:\n"
                "[\n"
                "  \"Requirement 1\",\n"
                "  \"Requirement 2\"\n"
                "]"
            )),
            ("user", "Client Document Text:\n\n{text}")
        ])
        
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
        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are an expert IT Solutions Architect, Mobile Developer, and AI/ML Consultant.\n"
                "Your job is to read the client RFP/document extremely carefully to understand all requirements, constraints, and scope.\n\n"
                "STEP 1: Identify the CORE application type described in the document. Is it a:\n"
                "- Web Application?\n"
                "- Mobile Application?\n"
                "- Data Engineering / ETL / Analytics Pipeline?\n"
                "- AI/ML or RAG Platform?\n"
                "- Desktop Application?\n"
                "Identify this based on details in the document.\n\n"
                "STEP 2: Recommend exactly 3 distinct technology options (packages) tailored specifically for that application type end-to-end.\n"
                "Choose the appropriate UI, backend, and database frameworks depending on the type:\n"
                "- For Mobile Apps: Recommends mobile UI frameworks (e.g., 'react_native', 'flutter', 'swift_ui', 'kotlin') for the UI field.\n"
                "- For Data Engineering: Recommends data/pipeline libraries (e.g., 'pyspark', 'dbt', 'apache_airflow') for the UI/Backend fields, and warehouse/caching (e.g. 'snowflake', 'cassandra', 'redis') for the Database field.\n"
                "- For AI/ML/RAG: Recommends AI-friendly backend APIs (e.g., 'fastapi', 'flask') and vector databases/caches (e.g. 'chromadb', 'pinecone', 'redis', 'arangodb').\n"
                "- For Web Apps: Recommends standard web tools (e.g. 'react', 'angular', 'vue', 'nestjs', 'flask', 'django', 'spring_boot', 'postgresql', 'mysql', 'mongodb').\n\n"
                "Requirements for the 3 options:\n"
                "- You must perform a deep analysis of the document to understand the true business and technical needs.\n"
                "- Do NOT force the options into arbitrary hardcoded categories. Instead, recommend the 3 most optimal, modern technology stacks that perfectly solve the specific problem described in the document.\n"
                "- Ensure each option is distinct, highly relevant, and practical for the client's actual use case.\n\n"
                "CRITICAL INSTRUCTION FOR AI APPLICATIONS:\n"
                "Check if the document or requirements mention artificial intelligence, machine learning, deep learning, LLMs, chatbots, RAG pipelines, agents, recommendations, or semantic search.\n"
                "If it is an AI application, you MUST include a list of the best AI models to use (e.g. GPT-4o, Claude 3.5 Sonnet, Llama 3.1 8B, Gemini 1.5 Pro, Cohere, etc.) in the 'ai_models' list. If it is NOT an AI application, leave 'ai_models' as an empty list [].\n\n"
                "Respond ONLY with a JSON object containing the following keys:\n"
                "1. 'extracted_technologies': An object with 'ui' (string or null), 'backend' (string or null), and 'database' (string or null) representing technologies explicitly requested in the document.\n"
                "2. 'tech_options': A list of exactly 3 objects. Each object represents an option and must have:\n"
                "   - 'id': String slug (e.g. 'option_1', 'option_2', 'option_3')\n"
                "   - 'name': Clear display name (e.g. 'Option 1: Modern Cross-Platform Mobile (Recommended)')\n"
                "   - 'ui': UI / Frontend / Mobile technology slug (e.g. 'react', 'react_native', 'flutter', 'swift_ui', 'angular', 'vue')\n"
                "   - 'backend': Backend technology or API framework slug (e.g. 'flask', 'django', 'express', 'nestjs', 'spring_boot', 'go_gin', 'fastapi')\n"
                "   - 'database': Database / Datastore / Cache / Warehouse technology slug (e.g. 'postgresql', 'mysql', 'mongodb', 'arangodb', 'sqlite', 'redis', 'snowflake')\n"
                "   - 'other_technologies': List of supporting tools/frameworks (e.g. ['Docker', 'Kubernetes', 'GitHub Actions', 'Redis', 'Tailwind CSS'])\n"
                "   - 'ai_models': A dynamic list of exactly 4-5 strings representing the best AI models to use for this specific stack if it's an AI/ML application. You MUST append ' and above' to each model name. DO NOT simply copy examples; you must actively select the best models (e.g., choosing specific versions from OpenAI, Anthropic, Google, Meta, or specialized open-source models) based on the exact problem domain. Otherwise an empty list [].\n"
                "   - 'rationale': One sentence explaining why this stack is a great fit for the client's requirements and the specific application type.\n"
                "3. 'chat_explanation': A detailed explanation in markdown format representing an AI chat response (RAG Chat style). "
                "It should introduce the 3 packages, explain the main chosen technologies (including AI model recommendations if applicable), why they are selected based on the requirements and application type, and how they integrate. Use bold text, lists, and a friendly, supportive consulting tone.\n\n"
                "Do not include any explanation or markdown formatting outside the JSON."
            )),
            ("user", "Requirements:\n{requirements}\n\nDocument snippet:\n{text}")
        ])
        
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
        Maps requirements to PwC competencies/assets, does gap analysis, and returns matched/gaps lists.
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
                prompt = ChatPromptTemplate.from_messages([
                    ("system", (
                        "You are a pre-sales consultant. Given a client requirement that we cannot fully "
                        "meet with existing assets, write exactly one sentence of mitigation (e.g. recruit a specialist "
                        "contractor or establish a new competence program)."
                    )),
                    ("user", "Client Requirement: {req}")
                ])
                chain = prompt | self.llm
                try:
                    res = chain.invoke({"req": req})
                    mitigation = res.content.strip()
                except Exception:
                    mitigation = "Address through temporary external contractor recruitment."
                gaps.append(f"Identified gap in Client Requirement: '{req}'. Mitigation: {mitigation}")

        if not gaps:
            gaps = ["No critical knowledge capability gaps identified. Full alignment with PwC competencies."]

        # Combine with LLM for final structure
        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are a technical consultant mapping client requirements to organization capabilities.\n"
                "Review the requirement mappings and identified gaps, and compile them into a clean JSON structure.\n"
                "Respond ONLY as a JSON object with two keys:\n"
                "- 'matched': a list of objects, each containing: 'requirement', 'asset_name', 'category', 'description'\n"
                "- 'gaps': a list of strings representing the identified gaps and mitigations.\n"
                "Do not include any markdown format blocks or introductory text."
            )),
            ("user", "Requirements: {reqs}\nMapped Assets: {assets}\nGaps List: {gaps}")
        ])
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
        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are an Enterprise Solutions Architect & Action Engine Agent.\n"
                "Analyze the document text and requirements to determine if advanced features are needed.\n"
                "Broadly interpret the concepts:\n"
                "1. RAG (Retrieval-Augmented Generation): Needed if you see concepts like 'Vector Knowledge Base', 'Semantic Engine', 'Vector Semantic Matching', 'Document Search', 'Embedding', or 'Retrieval'.\n"
                "2. Action Engine: Needed if you see mutating external actions like 'sending emails', 'writing to external databases', 'updating third-party records', or 'webhook triggers'.\n"
                "3. Guardrails (Data Protection): Needed if you see concepts like 'Sensitive Credential Masking', 'PII', 'Security Separation', 'Secret Variables', 'Data Protection', or 'Compliance'.\n\n"
                "Respond ONLY with a valid JSON object containing exactly three keys: 'rag_options', 'action_engine_options', and 'guardrail_options'.\n"
                "If a feature is needed based on the document, dynamically suggest 3-4 appropriate technology options for it.\n"
                "Each option must be a dictionary with an 'id' and 'name'.\n"
                "If a feature is NOT needed, its value must be an empty list [].\n"
                "Do NOT use markdown formatting, output raw JSON only."
            )),
            ("user", "Requirements:\n{requirements}\n\nDocument snippet:\n{text}")
        ])
        
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

