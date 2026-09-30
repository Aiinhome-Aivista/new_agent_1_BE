from langchain_core.prompts import ChatPromptTemplate

# ==========================================
# CENTRALIZED PROMPTS
# ==========================================

# Extracted from intake_agent.py
# This prompt classifies a document chunk into categories (e.g. Background, Requirements, etc).
INTAKE_AGENT_PROMPT_0 = ChatPromptTemplate.from_messages([
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

# Extracted from intake_agent.py

# This prompt extracts metadata like Client Name, Project Duration, and Budget from an RFP document.
INTAKE_AGENT_PROMPT_1 = ChatPromptTemplate.from_messages([
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

# Extracted from requirement_agent.py
# This prompt extracts the top 5 technical and business requirements from a document.
REQUIREMENT_AGENT_PROMPT_0 = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a pre-sales engineering assistant.\n"
        "Analyze the client document and extract the most important business and technical requirements.\n"
        "Determine the number of requirements dynamically based on the document complexity and content. "
        "Do not use a fixed number. Return only meaningful, non-duplicate requirements.\n"
        "Prioritize core business needs, functional requirements, technical requirements, "
        "security, integrations, performance, constraints, and delivery expectations when applicable.\n"
        "Do not invent requirements that are not supported by the document.\n"
        "Keep each requirement concise and presentation-ready.\n"
        "Respond ONLY as a JSON list of strings. No markdown or explanation."
    )),
    ("user", "Client Document Text:\n\n{text}")
])

# Extracted from requirement_agent.py
# This prompt analyzes the technology stack and recommends 3 options for UI, backend, and DB, along with AI models if applicable.
REQUIREMENT_AGENT_PROMPT_1 = ChatPromptTemplate.from_messages([
    (
        "system",
        (
            "You are an Enterprise Solution Architect analyzing a client RFP.\n\n"




            "IMPORTANT:\n"
            "Use ONLY the information contained in the provided CLIENT REQUIREMENTS and DOCUMENT TEXT.\n"
            "The document is the source of truth.\n"
            "Do not assume technologies, vendors, cloud platforms, frameworks, databases, "
            "AI models, integrations, or capabilities that are not supported by the document.\n"
            "Do not copy technologies from examples in this instruction.\n\n"




            "TASK:\n"
            "1. Carefully analyze the complete provided document text.\n"
            "2. Identify the actual application type, business requirements, technical requirements, "
            "constraints, integrations, security requirements, data requirements, and explicitly "
            "mentioned technologies.\n"
            "3. Extract technologies explicitly mentioned in the document.\n"
            "4. Based on the document context, generate exactly 3 technology stack options.\n\n"




            "TECHNOLOGY RECOMMENDATION RULES:\n"
            "- Recommendations must be dynamically derived from the document.\n"
            "- If a technology (like SharePoint) is explicitly mentioned for a layer (e.g. UI), use ONLY that technology for that layer. Do NOT mix it with others (e.g., do not output 'React, SharePoint').\n"
            "- If the document requires a UI/frontend but does NOT specify one, you MUST provide variety across the 3 options (e.g., React for Option 1, Angular for Option 2, Vue for Option 3).\n"
            "- If the document requires a backend API or Database but does NOT specify one, you MUST recommend appropriate technologies (e.g., Node.js, .NET, Java for backend; SQL Server, PostgreSQL for DB) to complete the stack, providing variety across options.\n"
            "- Do not assume AWS, Azure, GCP, PostgreSQL, MySQL, MongoDB, "
            "FastAPI, Flask, Spring Boot, or any other technology unless clearly required by the stated business or technical requirements.\n"
            "- If the document mentions a specific integration, platform, vendor, product, or service, "
            "make sure it is considered during the recommendation.\n"
            "- The three options should be meaningfully different but all must remain relevant to the document.\n"
            "- If the document does not explicitly specify enough technologies to form three distinct stacks, "
            "introduce alternatives only when they are directly justified by the documented requirements.\n\n"


            
            "IMPORTANT FOR EXPLICIT TECHNOLOGIES AND INTEGRATIONS:\n"
            "- Extract every explicitly mentioned technology, platform, product, vendor, service, integration, "
            "data source, framework, database, cloud service, or enterprise system from the document.\n"
            "- Preserve explicitly mentioned items exactly as they appear in the document whenever possible.\n"
            "- If an explicitly mentioned item is not a UI, backend, or database technology, place it in "
            "'other_technologies' rather than dropping it.\n"
            "- Do not omit an explicitly mentioned integration or platform such as an enterprise content system, "
            "collaboration platform, identity provider, cloud service, or external application.\n"
            "- Never replace an explicitly mentioned technology with a different technology unless the document "
            "clearly requires an alternative.\n"
            "- Every explicitly mentioned technology, platform, integration, vendor, product, or enterprise "
            "system must be preserved in the final analysis and must not be silently dropped.\n"
            "- If an explicitly mentioned item is not part of UI, backend, or database, place it under "
            "'other_technologies' rather than dropping it.\n\n"




            "EXPLICIT TECHNOLOGY EXTRACTION:\n"
            "The 'extracted_technologies' object must contain only technologies, platforms, products, "
            "vendors, services, integrations, data sources, frameworks, databases, cloud services, "
            "and enterprise systems explicitly mentioned in the DOCUMENT TEXT.\n"
            "Do not infer, recommend, or add technologies to this object.\n"
            "Classify explicitly mentioned items into 'ui', 'backend', 'database', or 'other'.\n"
            "If an enterprise platform like SharePoint, PowerApps, or Salesforce is mentioned as the primary user interface or frontend, you MUST classify it strictly under 'ui'.\n"
            "Any other explicitly mentioned item that does not clearly belong to UI, backend, or database "
            "must be placed in 'other'.\n"
            "Preserve the original name from the document whenever possible.\n\n"




            "AI MODEL RULES:\n"
            "- Only include AI models when the document requires or discusses AI/ML/LLM functionality.\n"
            "- If specific model names are explicitly mentioned, return only those models and mark them "
            "as '(Mentioned in INPUT Document)'.\n"
            "- If no model is mentioned but AI is required, recommend suitable models based on the "
            "actual documented use case.\n"
            "- Do not recommend AI models when the document does not require AI functionality.\n\n"




            "OUTPUT:\n"
                "Return ONLY valid JSON with exactly these keys:\n"
                "{{\n"
                '  "extracted_technologies": {{\n'
                '    "ui": [],\n'
                '    "backend": [],\n'
                '    "database": [],\n'
                '    "other": []\n'
                "  }},\n"
                '  "tech_options": [\n'
                "    {{\n"
                '      "id": "option_1",\n'
                '      "name": "...",\n'
                '      "ui": "...",\n'
                '      "backend": "...",\n'
                '      "database": "...",\n'
                '      "other_technologies": [],\n'
                '      "ai_models": [],\n'
                '      "rationale": "..."\n'
                "    }}\n"
                "  ],\n"
                '  "chat_explanation": "..."\n'
                "}}\n\n"



            "The response must be grounded in the supplied document. "
            "Do not include unsupported technologies."
        )
    ),
    (
        "user",
        (
            "CLIENT REQUIREMENTS:\n{requirements}\n\n"
            "COMPLETE DOCUMENT TEXT:\n{text}\n\n"
            "Analyze the document carefully and generate the technology recommendations "
            "strictly from the supplied content."
        )
    )
])

# Extracted from requirement_agent.py
# This prompt generates a mitigation strategy (1 sentence) for a client requirement that cannot be met by existing assets.
REQUIREMENT_AGENT_PROMPT_2 = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a pre-sales consultant. "
        "For the given client requirement, write one concise, specific mitigation strategy "
        "that explains how the capability gap can be addressed. "
        "Use the requirement itself to determine the appropriate mitigation, such as internal development, "
        "specialist hiring, partner support, training, tooling, or third-party expertise. "
        "Avoid generic phrases, repetition, and phrases such as 'our current limitations'. "
        "Return only one professional sentence suitable for an executive proposal slide."
    )),
    ("user", "Client Requirement: {req}")
])

# Extracted from requirement_agent.py
# This prompt evaluates if client requirements can be solved by an asset and compiles a final matching report.
REQUIREMENT_AGENT_PROMPT_3 = ChatPromptTemplate.from_messages([
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

# Extracted from requirement_agent.py
# This prompt extracts constraints like compliance, SLA, scalability, and proposes advanced options (RAG, Action Engines, Guardrails).
REQUIREMENT_AGENT_PROMPT_4 = ChatPromptTemplate.from_messages([
    (
        "system",
        (
            "You are an Enterprise Solutions Architect analyzing an RFP.\n\n"


            "The provided document is the only source of truth.\n"
            "Analyze the actual requirements, technologies, integrations, security needs, "
            "data flows, workflows, and business processes described in the document.\n\n"


            "Determine the best technologies for the following capability areas:\n"
            "1. RAG / Retrieval\n"
            "2. Action Engine / Agentic Workflow\n"
            "3. Guardrails / Data Protection\n\n"


            "IMPORTANT:\n"
            "- If the document explicitly mentions a technology, platform, vendor, framework, "
            "database, cloud service, or product for these areas, preserve it in the relevant option list and mark it as '(Mentioned in INPUT)'.\n"
            "- If the document does not explicitly specify technologies for these capabilities, you MUST dynamically "
            "recommend 2-3 suitable best-practice technologies based on the application's actual environment.\n"
            "- Provide a variety of suitable options (e.g., open-source vs enterprise, different cloud providers if applicable).\n"
            "- Recommendations must be relevant to the application's overall context and goals.\n\n"


            "RAG:\n"
            "Recommend the best vector databases, semantic search engines, or document retrieval systems (e.g., Pinecone, Weaviate, Azure AI Search, FAISS).\n\n"


            "ACTION ENGINE:\n"
            "Recommend the best agentic frameworks, workflow automation tools, or orchestration engines (e.g., LangChain, AutoGen, CrewAI, Semantic Kernel).\n\n"


            "GUARDRAILS:\n"
            "Recommend the best data protection, PII masking, and security guardrail tools (e.g., NeMo Guardrails, Llama Guard, Presidio, Custom Data Masking).\n\n"


            "OUTPUT:\n"
            "Return ONLY valid JSON with exactly these keys:\n"
            "{{\n"
            '  "rag_options": [],\n'
            '  "action_engine_options": [],\n'
            '  "guardrail_options": []\n'
            "}}\n\n"


            "Each option must contain:\n"
            "- id (e.g., 'rag_1')\n"
            "- name (e.g., 'Pinecone')\n\n"


            "Always return at least 1-3 recommended options for each capability area, even if they are not explicitly required by the document."
        )
    ),
    (
        "user",
        (
            "CLIENT REQUIREMENTS:\n{requirements}\n\n"
            "COMPLETE DOCUMENT TEXT:\n{text}\n\n"
            "Analyze the document and return the best capability recommendations."
        )
    )
])

# Extracted from design_agent.py
# This is the main Tree-of-Thoughts (ToT) prompt that designs the system architecture, business summary, pillars, data flow, and infrastructure cost.
DESIGN_AGENT_PROMPT_0 = ChatPromptTemplate.from_messages([
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
                "- 'business_summary': Write a professional executive-level business summary in exactly 3 well-developed paragraphs, "
                "approximately 180-220 words. Explain the client's business need/problem, the proposed solution and its key business capabilities, "
                "and the expected business benefits/strategic impact. Keep it specific to the RFP and avoid generic statements. "
                "Focus strictly on business value and outcomes. Do not mention technologies, frameworks, databases, APIs, architecture, RAG, "
                "AI models, or infrastructure. Do not invent features, ROI, percentages, cost savings, or other benefits not supported by the RFP. "
                "Do not produce a short summary or bullet list.\n"
                "- 'solution_pillars': a list of exactly 3 objects representing the three most important solution capabilities "
                "for the client's specific requirements. Each object must contain 'title' and 'desc'. "
                "The titles and descriptions must be derived dynamically from the RFP and should represent distinct business capabilities. "
                "Each 'desc' should contain 2-3 concise sentences, approximately 30-45 words, explaining what the capability does, "
                "how it addresses the client's requirements, and its business value. "
                "Do not use generic or repetitive pillars, and do not invent capabilities that are not supported by the RFP. "
                "Do not mention specific technologies unless they are directly relevant to explaining the solution capability.\n"
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
                "  * 'tech_architecture_explanation': a list of exactly 3 strings representing extremely short and concise summaries (exactly 1 sentence, maximum 12 words per summary) of: 1. Source/Ingestion, 2. Storage/Processing, and 3. Consumption/Reporting. They must fit in a very small box.\n"
                "  * 'key_technologies': a list of exactly 3-4 technologies used (e.g. ['Snowflake', 'Azure Data Factory']).\n"
                "  * 'benefits_outcome': a list of exactly 3-4 strings summarizing benefits and outcomes.\n"
                "- 'complex_diagrams': a list of exactly 2 objects representing logical system architecture diagrams for the proposed client solution (NOT the proposal creator app itself). "
                "The first object must be for the Logical Reference Architecture (title: 'Reference Architecture') representing the logical end-to-end data/component flow of the proposed solution. "
                "The second object must be for the Cloud Native Deployment Landscape (title: 'Landscape Architecture') representing the topology of the proposed solution on the selected cloud platform (e.g. AWS, Azure, or GCP). "
                "Each object must have these keys:\n"
                "  * 'title': the title of the diagram.\n"
                "  * 'mermaid_code': a valid, clean Mermaid.js flowchart (starting with 'graph LR' for optimal wide layout) representing that specific architecture of the proposed solution. Follow these strict syntax rules:\n"
                "    1. Start with 'graph LR'.\n"
                "    2. Use clear, alphanumeric node IDs (e.g., UI, API, DB).\n"
                "    3. Enclose all text labels in double quotes (e.g., UI[\"Web UI (Angular or relevant UI technology mentioned in the attached document)\"] or DB[(\"PostgreSQL Database\")]) to avoid rendering errors. Do NOT use brackets or parentheses without double quotes around the label text inside the node.\n"
                "    4. Use standard connectors like --> and subgraph boxes for different layers (e.g. Ingestion, Compute, Storage).\n"
                "    5. Do NOT include style declarations, class definitions, or CSS inside the Mermaid code.\n"
                "    6. THE DIAGRAMS MUST BE COMPLETELY DIFFERENT: The 'Reference Architecture' diagram must show generic, logical tiers and data ingestion/processing pipelines (e.g. 'API Gateway', 'Core API Server', 'Cache', 'Object Storage', 'Vector Database', 'Message Queue', 'Auth Service'). "
                "The 'Landscape Architecture' diagram must map these logical components to actual cloud-native deployment resources of the target cloud provider (identify the provider from the RFP text, e.g. AWS, Azure, or GCP, defaulting to Azure if not specified). E.g. for Azure use 'Azure API Management', 'Azure App Service', 'Azure Cache for Redis', 'Azure Blob Storage', 'Azure Cognitive Search', 'Azure Monitor', organized in clean subgraphs representing VPC/VNet zones, API layer, database layer, and monitoring.\n"
                "    7. BE DETAILED: Make the flowcharts comprehensive (at least 6-10 nodes each) reflecting the specific needs in the RFP document context (e.g., if database migration is requested, show source systems, transfer utility, target cloud database; if RAG is requested, show document ingestion, vector storage, LLM orchestration, client UI).\n\n"
                "- 'technical_key_points': a list of 4-6 objects representing the immediate technical needs for Phase 1 implementation. "
                "Each object must contain a 'title' and a 'bullets' list with 2-4 concise but meaningful technical action points. "
                "The points must be specific to the client's RFP and should cover the most important immediate areas such as core system implementation, "
                "security and compliance, data management, integrations, authentication/access control, infrastructure, monitoring, performance, "
                "or other technically relevant areas identified in the RFP. "
                "Do not generate generic points that are not supported by the RFP. "
                "Keep each bullet concise and action-oriented so it fits naturally on a presentation slide.\n"
                "- 'technical_key_points_mermaid': optional mermaid flowchart string for the technical key points.\n"
                "- 'approach_steps': a list of 4-5 objects representing the complete project execution approach from discovery through deployment and handover. "
                "Each object must contain a 'phase' and a 'bullets' list with 2-3 concise but meaningful activities. "
                "The phases should follow a logical project lifecycle based on the RFP, such as Discovery & Design, Development, Integration & Testing, "
                "User Acceptance & Deployment, and Go-Live & Handover. "
                "Adapt the phases to the actual project requirements rather than blindly using these names. "
                "Each bullet must describe a specific project activity or deliverable relevant to the client's RFP. "
                "Do not generate generic or repetitive activities. Keep the bullets concise and suitable for an executive presentation slide.\n"
                "- 'understanding_in_scope': a list of 4-6 objects representing the major functional/business modules that are explicitly or clearly supported as being within the project scope. "
                "Each object must contain 'module', 'access', and 'points'. "
                "'access' should identify the relevant user role such as Admin, User, Manager, or N/A. "
                "Each 'points' list should contain 2-4 concise and specific scope items derived from the RFP. "
                "Group related requirements under meaningful modules instead of creating one module per individual requirement. "
                "Do not invent modules or capabilities that are not supported by the RFP.\n"

                "- 'understanding_out_scope': a list of 3-5 objects representing major capabilities, integrations, systems, or activities that are explicitly excluded from the project scope or clearly identified as outside the stated requirements. "
                "Each object must contain 'module', 'access', and 'points'. "
                "Each 'points' list should contain 1-3 concise and specific out-of-scope items supported by the RFP. "
                "Do not assume something is out of scope merely because it is not mentioned; include it only when the RFP explicitly excludes it or provides sufficient evidence that it is outside the project scope.\n"
                "- 'considerations': a list of 4-6 objects representing the key assumptions, dependencies, risks, constraints, and operational considerations relevant to the project. "
                "Each object must contain a 'title' and a 'bullets' list with 2-3 concise and specific points. "
                "Cover different relevant areas such as data migration, infrastructure, security and compliance, integrations, "
                "business/user readiness, dependencies, operational support, or project constraints, but only when supported by the RFP. "
                "Prioritize the considerations that could affect project delivery, implementation, adoption, or ongoing operations. "
                "Do not invent assumptions or risks that are not supported or reasonably implied by the RFP. "
                "Keep each bullet concise, specific, and suitable for an executive presentation slide.\n"
            )),
            (
                "user",
                "CLIENT REQUIREMENTS:\n{requirements}\n\n"
                "RFP DOCUMENT CONTENT:\n{full_rfp_text}\n\n"
                "BUDGET:\n{budget}\n\n"
                "PROJECT DURATION:\n{duration}\n\n"
                "CASE STUDY DOCUMENTS:\n{case_study_text}\n\n"
                "Generate the business_summary primarily from the client requirements and RFP document content. "
                "Make the summary specific to the client's actual business need and proposed solution."
            )
        ])
# Extracted from orchestrator.py
ORCHESTRATOR_SYS_PROMPT_0 = (
        "You are an assistant that classifies document sections from an RFP.\n"
        "Classify the text into exactly one of these labels:\n"
        "- Background\n"
        "- Requirements\n"
        "- Financial & Sizing\n"
        "- Compliance & Security\n"
        "- Other\n"
        "Respond ONLY with the selected label (e.g. 'Requirements'). No markdown, punctuation or explanation."
)

# Extracted from orchestrator.py
# This prompt plans the timeline and resource allocation for the proposal to match the target budget exactly.
ORCHESTRATOR_SYS_PROMPT_1 = (
                            "You are an expert bid manager. Extract the following details from this case study text to create a structured project summary.\n"
                            "Respond ONLY as a JSON object with these keys:\n"
                            "  * 'project_name': short name of the project.\n"
                            "  * 'client_industry': industry/details of the client.\n"
                            "  * 'business_problem': a list of exactly 3-4 strings representing key business/technical challenges.\n"
                            "  * 'our_approach': a list of exactly 3-4 strings detailing the steps or architectural choices built to solve it.\n"
                            "  * 'tech_architecture_mermaid': a valid, clean Mermaid.js flowchart (starting with 'graph LR') representing the technical architecture.\n"
                            "  * 'tech_architecture_explanation': a list of exactly 3 strings representing concise summaries (1-2 sentences) of: 1. Source/Ingestion, 2. Storage/Processing, and 3. Consumption/Reporting.\n"
                            "  * 'key_technologies': a list of exactly 3-4 technologies used.\n"
                            "  * 'benefits_outcome': a list of exactly 3-4 strings summarizing benefits and outcomes.\n\n"
                            "Do not include any formatting or text outside the JSON."
                        )



# Extracted from case_study_controller.py
CASE_STUDY_CONTROLLER_SYS_PROMPT_1 = (
                "You are an expert Solutions Architect. Parse the provided case study document text "
                "and format it into a structured JSON object representing a detailed case study.\n\n"
                "Your response must ONLY be a JSON object with these keys:\n"
                "- project_name\n"
                "- client_industry\n"
                "- business_problem\n"
                "- our_approach\n"
                "- tech_architecture_mermaid\n"
                "- tech_architecture_explanation (a list of exactly 3 strings representing extremely short and concise summaries, maximum 1 sentence and 12 words each: 1. Source/Ingestion, 2. Storage/Processing, and 3. Consumption/Reporting)\n"
                "- key_technologies\n"
                "- benefits_outcome\n"
                "Return ONLY JSON."
            )

# Extracted from llm_client.py
# This prompt extracts basic metadata from an internal document to classify it as an Asset or Competency in ChromaDB.
LLM_CLIENT_SYS_PROMPT_0 = (
        "You are an assistant that analyzes technical documents or competencies.\n"
        "Extract the following metadata from the text:\n"
        "1. category: Must be exactly 'Asset' or 'Competency'. If the document describes a reusable tool, package, framework, template, or toolkit, classify as 'Asset'. If it describes team skills, services, capability profiles, or competencies, classify as 'Competency'.\n"
        "2. Extract specific metadata details from the document: Domain, Tech Stack, Industry, Solution Type, Architecture, Client Organization (optional), Application Type (e.g., mobile app or web app), and Dates (e.g., project dates, release dates, years).\n"
        "3. tags: Consolidate all the valid values extracted in step 2 along with any other key technical skills, programming languages, tools, or dates mentioned into a flat list of strings. Do not include null or empty values.\n"
        "4. description: A 1-2 sentence summary of what the document or competency is about, highlighting any key deliverables or cost structure if mentioned.\n"
        "Respond ONLY as a JSON object with three keys: 'category', 'tags', and 'description'. Do not include any explanation or markdown wrappers."
    )

# Extracted from pricing_kb.py
# This prompt calculates the total software development budget cost based on the selected tech stack.
PRICING_KB_SYS_PROMPT_0 = (
        "You are an IT solution architect. Given a list of technical skills or tools, "
        "categorize each skill into exactly one of three groups: 'ui' (frontend/UI/styling framework), "
        "'backend' (backend/API/server framework/runtime), or 'database' (databases/caching/datastores).\n"
        "Ignore other non-UI/non-backend/non-database keywords like AWS, Azure, DevOps, Terraform, Ansible, Migration, etc.\n"
        "Respond ONLY with a JSON object containing three keys: 'ui', 'backend', and 'database'.\n"
        "Under each key, provide a list of objects with 'value' (lowercase slug, e.g. 'react') and 'label' (nice display name, e.g. 'React.js').\n"
        "Example format:\n"
        "{\n"
        "  \"ui\": [{\"value\": \"react\", \"label\": \"React.js\"}],\n"
        "  \"backend\": [{\"value\": \"flask\", \"label\": \"Flask (Python)\"}],\n"
        "  \"database\": [{\"value\": \"mysql\", \"label\": \"MySQL\"}]\n"
        "}\n"
        "Do not include any explanation or markdown formatting."
    )

# Extracted from pricing_kb.py
# This prompt classifies technical skills into specific categories like UI, Backend, Database, Infrastructure, or Exclude.
PRICING_KB_SYS_PROMPT_2 = (
        "You are a technical presales estimator. You need to calculate the total software development budget based on the selected tech stack.\n"
        "Read the provided Knowledge Base Context to find the cost associated with each technology. If a technology's cost is missing, estimate it reasonably (e.g., $15000).\n"
        "Include a base platform setup cost of $15000.\n"
        "Respond ONLY as a JSON object with two keys:\n"
        "- 'total_cost': an integer representing the total sum.\n"
        "- 'formatted_budget': a string formatted as currency (e.g., '$75,000').\n"
        "Do not include markdown or explanations."
    )

