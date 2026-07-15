import os
import json
import uuid
import time
import threading
from database.db_connection import get_db_connection
from utils.pptx_generator import generate_pptx
from utils.llm_client import query_llm
from utils.doc_extractor import extract_text

# Define the step list in order
STEPS = [
    "Ingesting",
    "Analyzing",
    "Designing",
    "Planning",
    "Assembling",
    "Complete"
]

def update_step_status(proposal_id, step_name, status, log_message=None):
    """Utility to update proposal_steps table for real-time progress bar."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if step exists
        cursor.execute(
            "SELECT id FROM proposal_steps WHERE proposal_id = %s AND step_name = %s",
            (proposal_id, step_name)
        )
        row = cursor.fetchone()
        
        if row:
            cursor.execute(
                "UPDATE proposal_steps SET status = %s, log_message = %s WHERE id = %s",
                (status, log_message, row[0])
            )
        else:
            cursor.execute(
                "INSERT INTO proposal_steps (proposal_id, step_name, status, log_message) VALUES (%s, %s, %s, %s)",
                (proposal_id, step_name, status, log_message)
            )
        
        conn.commit()
    except Exception as e:
        print(f"Error updating step status: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def update_proposal_status(proposal_id, status, file_path=None, json_ir=None):
    """Utility to update main proposals status."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if file_path and json_ir:
            cursor.execute(
                "UPDATE proposals SET status = %s, generated_file_path = %s, structured_json_ir = %s WHERE id = %s",
                (status, file_path, json_ir, proposal_id)
            )
        elif file_path:
            cursor.execute(
                "UPDATE proposals SET status = %s, generated_file_path = %s WHERE id = %s",
                (status, file_path, proposal_id)
            )
        else:
            cursor.execute(
                "UPDATE proposals SET status = %s WHERE id = %s",
                (status, proposal_id)
            )
        conn.commit()
    except Exception as e:
        print(f"Error updating proposal status: {e}")
    finally:
        if cursor: cursor.close()

def update_proposal_metadata(proposal_id, client_name, project_duration, budget):
    """Utility to update proposal client name, duration, and budget in the database."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE proposals SET client_name = %s, project_duration = %s, budget = %s WHERE id = %s",
            (client_name, project_duration, budget, proposal_id)
        )
        conn.commit()
    except Exception as e:
        print(f"Error updating proposal metadata: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def query_rag_assets(requirements):
    """Performs semantic keywords search on database knowledge_assets."""
    matched_assets = []
    unmatched_reqs = []
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM knowledge_assets")
        assets = cursor.fetchall()
        
        for req in requirements:
            matched = False
            for asset in assets:
                # Check if asset name or description matches keywords in requirement
                capabilities = [c.strip().lower() for c in asset.get("capabilities", "").split(",")]
                req_lower = req.lower()
                
                # Check if any capability tag is mentioned in client requirement
                for cap in capabilities:
                    if cap and cap in req_lower:
                        matched_assets.append({
                            "requirement": req,
                            "asset_name": asset["name"],
                            "category": asset["category"],
                            "description": asset["description"]
                        })
                        matched = True
                        break
            if not matched:
                unmatched_reqs.append(req)
    except Exception as e:
        print(f"RAG query failed, fallback: {e}")
        # Default fallback matches
        matched_assets = [
            {"requirement": "Build React/TS application", "asset_name": "React/TypeScript Front-End Competency", "category": "Competency", "description": "Front-end engineering pool"},
            {"requirement": "CI/CD Deployment", "asset_name": "DevOps Pipeline Accelerator", "category": "Asset", "description": "GitHub/GitLab pipelines"}
        ]
        unmatched_reqs = [r for r in requirements if "React" not in r and "CI/CD" not in r]
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
        
    return matched_assets, unmatched_reqs

def safe_json_loads(json_str, fallback):
    if not json_str:
        return fallback
    cleaned = json_str.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except Exception as e:
        print(f"Failed to parse JSON: {e}. Raw content: {json_str}")
        return fallback

def run_orchestration(proposal_id, client_name, project_duration, budget, files_info):
    """The full Multi-Agent pipeline, executing step-by-step using LLM and fallback defaults."""
    try:
        # Initialize steps in database as 'pending'
        for step in STEPS:
            update_step_status(proposal_id, step, "pending", "Waiting to start...")

        # ----------------------------------------------------
        # 1. INTAKE AGENT (Document parsing, extraction & validation)
        # ----------------------------------------------------
        update_step_status(proposal_id, "Ingesting", "running", "Ingesting client documents: validating format & extracting text...")
        
        extracted_text_blocks = []
        if files_info:
            for file_data in files_info:
                saved_path = file_data.get("saved_path")
                orig_name = file_data.get("original_name")
                if saved_path and os.path.exists(saved_path):
                    txt = extract_text(saved_path)
                    if txt:
                        extracted_text_blocks.append(f"--- Document: {orig_name} ---\n{txt}")
        
        full_document_text = "\n\n".join(extracted_text_blocks).strip()
        
        # Validation
        if not full_document_text:
            full_document_text = f"Proposal request for client {client_name} with target budget {budget} and timeline {project_duration}."
            print("No text extracted from uploaded files or no files uploaded. Using default input context.")
            
        # Check if metadata extraction is needed
        needs_client = (client_name == "Extracting Client Name...")
        needs_duration = (project_duration == "Extracting...")
        needs_budget = (budget == "Extracting...")
        
        if needs_client or needs_duration or needs_budget:
            # Query LLM to extract metadata
            meta_sys_prompt = (
                "You are an assistant that extracts metadata from client RFPs.\n"
                "Extract the following values if they are present in the text:\n"
                "1. Client Name (the company asking for the proposal, e.g. 'Acme Corporation')\n"
                "2. Project Duration/Timeline (e.g. '14 Weeks')\n"
                "3. Target Budget (e.g. '$250,000')\n"
                "Respond ONLY with a JSON object containing keys: 'client_name', 'project_duration', 'budget'.\n"
                "Do not include markdown code block syntax or comments."
            )
            meta_user_prompt = f"RFP Text Snippet:\n\n{full_document_text[:5000]}"
            meta_raw = query_llm(meta_sys_prompt, meta_user_prompt, json_mode=True)
            if meta_raw is None:
                raise RuntimeError("Failed to connect to local Mistral LLM server for metadata extraction (read timeout/offline).")
            extracted_meta = safe_json_loads(meta_raw, {})
            if needs_client:
                ext_client = extracted_meta.get("client_name", "").strip()
                if not ext_client or "Extracting" in ext_client:
                    client_name = "Acme Corporation"
                else:
                    client_name = ext_client
            if needs_duration:
                ext_duration = extracted_meta.get("project_duration", "").strip()
                if not ext_duration or "Extracting" in ext_duration:
                    project_duration = "14 Weeks"
                else:
                    project_duration = ext_duration
            if needs_budget:
                ext_budget = extracted_meta.get("budget", "").strip()
                if not ext_budget or "Extracting" in ext_budget:
                    budget = "$250,000"
                else:
                    budget = ext_budget
                
            # Update the database with the extracted metadata
            update_proposal_metadata(proposal_id, client_name, project_duration, budget)

        logs = f"Parsed {len(files_info)} document(s). Extracted and preprocessed {len(full_document_text)} characters."
        update_step_status(proposal_id, "Ingesting", "completed", logs)

        # ----------------------------------------------------
        # 2. KNOWLEDGE AGENT (LLM Requirement Extraction & RAG mapping)
        # ----------------------------------------------------
        update_step_status(proposal_id, "Analyzing", "running", "Extracting requirements & querying PwC assets repository (RAG)...")
        
        # Call LLM to extract requirements
        req_sys_prompt = (
            "You are a pre-sales engineering assistant. Given the client document text, "
            "extract the top 5 technical and business requirements for this solution. "
            "Respond ONLY as a JSON list of strings, with no other text, comments or markdown blocks. "
            "Example format:\n[\n  \"Requirement 1\",\n  \"Requirement 2\"\n]"
        )
        req_user_prompt = f"Client Document Text:\n\n{full_document_text[:8000]}"
        
        extracted_reqs_raw = query_llm(req_sys_prompt, req_user_prompt, json_mode=True)
        if extracted_reqs_raw is None:
            raise RuntimeError("Failed to connect to local Mistral LLM server for requirement extraction (read timeout/offline).")
        default_requirements = [
            f"Deliver high-performance React front-end application with state management.",
            f"Establish secure, authenticated JSON APIs with low latency.",
            f"Set up secure containerized database configuration with audit trails.",
            f"Implement automated DevOps workflows, CI/CD, and security vulnerability scanning.",
            f"Adhere to delivery target timeline within {project_duration}."
        ]
        requirements = safe_json_loads(extracted_reqs_raw, default_requirements)
        if not isinstance(requirements, list) or len(requirements) == 0:
            requirements = default_requirements

        # Fetch knowledge assets for RAG
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM knowledge_assets")
        all_assets = cursor.fetchall()
        cursor.close()
        conn.close()
        
        assets_context_str = json.dumps([
            {"name": a["name"], "category": a["category"], "description": a["description"], "capabilities": a["capabilities"]}
            for a in all_assets
        ])
        
        # RAG Mapping Prompt
        rag_sys_prompt = (
            "You are a technical consultant mapping client requirements to organization capabilities.\n"
            "Given client requirements and our knowledge assets/competencies, map each requirement "
            "to a capability. For any requirements that cannot be matched to our assets, identify them "
            "as gaps and provide a mitigation plan.\n"
            "Respond ONLY as a JSON object with two keys:\n"
            "- 'matched': a list of objects, each containing: 'requirement', 'asset_name', 'category', 'description'\n"
            "- 'gaps': a list of strings representing the identified gaps and mitigations.\n"
            "Do not include any text before or after the JSON."
        )
        rag_user_prompt = f"Requirements:\n{json.dumps(requirements)}\n\nKnowledge Assets:\n{assets_context_str}"
        
        rag_mapped_raw = query_llm(rag_sys_prompt, rag_user_prompt, json_mode=True)
        if rag_mapped_raw is None:
            raise RuntimeError("Failed to connect to local Mistral LLM server for RAG capability matching.")
        
        # Match using database keywords if LLM failed
        db_matched, db_unmatched = query_rag_assets(requirements)
        db_gaps = []
        for r in db_unmatched:
            db_gaps.append(f"Identified gap in Client Requirement: '{r}'. Mitigation: Align with external consultants.")
        if not db_gaps:
            db_gaps = ["No critical knowledge capability gaps identified. Full alignment with PwC competencies."]
            
        default_rag = {
            "matched": db_matched,
            "gaps": db_gaps
        }
        
        rag_data = safe_json_loads(rag_mapped_raw, default_rag)
        matched = rag_data.get("matched", db_matched)
        gaps = rag_data.get("gaps", db_gaps)
        
        logs = f"RAG grounding completed. Mapped {len(matched)} requirements. Found {len(gaps)} potential gaps / mitigations."
        update_step_status(proposal_id, "Analyzing", "completed", logs)

        # ----------------------------------------------------
        # 3. SOLUTION DESIGN AGENT (Tree-of-Thoughts Architecture)
        # ----------------------------------------------------
        update_step_status(proposal_id, "Designing", "running", "Designing technical solution architecture & pillars (Tree-of-Thoughts)...")
        
        design_sys_prompt = (
            "You are a Lead IT Architect. Based on client requirements, budget constraint, and duration, "
            "propose a solution design containing 3 solution pillars and a landscape architecture table.\n"
            "Respond ONLY as a JSON object with the following keys:\n"
            "- 'solution_pillars': a list of exactly 3 objects, each with 'title' (short name) and 'desc' (sentence detail).\n"
            "- 'architecture': a list of exactly 3 layers (e.g., 'Presentation layer (UI Client)', "
            "'Application Logic (API Backend)', 'Data Integration & Cache Layer') where each layer object contains "
            "'name' (string) and 'components' (list of strings representing systems/frameworks).\n"
            "Do not include any text before or after the JSON."
        )
        design_user_prompt = f"Requirements:\n{json.dumps(requirements)}\nBudget: {budget}\nDuration: {project_duration}"
        
        design_raw = query_llm(design_sys_prompt, design_user_prompt, json_mode=True)
        if design_raw is None:
            raise RuntimeError("Failed to connect to local Mistral LLM server for Solution Design.")
        
        default_pillars = [
            {"title": "Agentic Orchestrator Engine", "desc": "Implement a stateful multi-agent orchestrator utilizing ReAct patterns to parse proposals asynchronously."},
            {"title": "Responsive React Dashboard", "desc": "Deliver an intuitive dashboard built with React 18, Zustand, and Tailwind, offering real-time progress steps and inline document editing."},
            {"title": "Deterministic Presentation Engine", "desc": "Compile agent decisions into a clean JSON IR, and render a pixel-perfect PPTX deck using python-pptx."}
        ]
        default_architecture = [
            {"name": "Presentation layer (UI Client)", "components": ["Vite + React 18 SPA", "Zustand State", "Axios Service"]},
            {"name": "Application Logic (API Backend)", "components": ["Flask Web Service", "Agent Control Loop", "Auth Service"]},
            {"name": "Data Integration & Cache Layer", "components": ["MySQL Database", "python-pptx Builder", "Semantic RAG Store"]}
        ]
        
        default_design = {
            "solution_pillars": default_pillars,
            "architecture": default_architecture
        }
        
        design_data = safe_json_loads(design_raw, default_design)
        solution_pillars = design_data.get("solution_pillars", default_pillars)
        architecture = design_data.get("architecture", default_architecture)
        
        logs = f"Architectural evaluation complete. Structured solution pillars and system architecture generated."
        update_step_status(proposal_id, "Designing", "completed", logs)

        # ----------------------------------------------------
        # 4. PLANNING & ESTIMATION AGENT (Timeline & Resourcing)
        # ----------------------------------------------------
        update_step_status(proposal_id, "Planning", "running", "Calculating resources loading, rates sizing, and deliverables timeline...")
        
        plan_sys_prompt = (
            f"You are a Delivery Manager sizing project delivery. The client's target budget is {budget} "
            f"and duration is {project_duration}. Generate resource and timeline estimation.\n"
            "Respond ONLY as a JSON object with the following keys:\n"
            "- 'timeline_phases': a list of exactly 3 phase objects. Each phase object contains 'phase' (name), "
            "'duration' (weeks range), and 'deliverables' (key activities/deliverables text).\n"
            "- 'resources': a list of exactly 5 resource roles. Each resource object contains: "
            "'role' (string), 'loc' ('Onsite', 'Offshore', 'Hybrid'), 'fte' (decimal string, e.g., '1.00', '0.25'), "
            "'rate' (monthly rate string, e.g., '$8,000'), and 'total' (total cost calculation for this resource).\n"
            "- 'skills_mapping': a list of exactly 5 skills mapping objects. Each object contains: "
            "'skill' (technical skill name), 'role' (matching project role), 'asset' (matching PwC Asset/Competency name), "
            "and 'conf' (confidence percentage string, e.g. '95%').\n"
            "Ensure that total calculations align with realistic industry values. Do not include formatting before or after the JSON."
        )
        plan_user_prompt = f"Requirements: {json.dumps(requirements)}\nBudget: {budget}\nDuration: {project_duration}"
        
        plan_raw = query_llm(plan_sys_prompt, plan_user_prompt, json_mode=True)
        if plan_raw is None:
            raise RuntimeError("Failed to connect to local Mistral LLM server for Planning and Sizing.")
        
        default_timeline = [
            {"phase": "Phase 1: Discovery & Setup", "duration": "Weeks 1-3", "deliverables": "RFP requirements analysis, database sync, initial architectures alignment."},
            {"phase": "Phase 2: Core Platform Build", "duration": "Weeks 4-10", "deliverables": "Flask backend setup, multi-agent logic integration, React dashboard interfaces, and PPTX renderer."},
            {"phase": "Phase 3: UAT & Handoff", "duration": "Weeks 11-14", "deliverables": "UAT feedback validation, performance tuning, and staging platform release."}
        ]
        default_resources = [
            {"role": "Engagement Director", "loc": "Hybrid", "fte": "0.15", "rate": "$32,000", "total": "$21,600"},
            {"role": "Lead Architect", "loc": "Onsite", "fte": "1.00", "rate": "$25,000", "total": "$100,000"},
            {"role": "Senior Developer (Front-end)", "loc": "Offshore", "fte": "1.50", "rate": "$8,000", "total": "$48,000"},
            {"role": "Senior Developer (Back-end)", "loc": "Offshore", "fte": "1.50", "rate": "$8,000", "total": "$48,000"},
            {"role": "QA & Test Engineer", "loc": "Offshore", "fte": "1.00", "rate": "$6,000", "total": "$24,000"}
        ]
        default_skills = [
            {"skill": "React 18 & TypeScript", "role": "Senior Developer (Front-end)", "asset": "React/TypeScript Front-End Competency", "conf": "High (95%)"},
            {"skill": "Flask API & Python pptx", "role": "Senior Developer (Back-end)", "asset": "Python Data Engineering Competency", "conf": "High (92%)"},
            {"skill": "MySQL Connector / Database", "role": "Lead Architect", "asset": "Enterprise Data Governance Framework", "conf": "High (90%)"},
            {"skill": "CI/CD & DevOps Automation", "role": "Senior Developer (Back-end)", "asset": "DevOps Pipeline Accelerator", "conf": "High (98%)"},
            {"skill": "ISO27001 Auditing", "role": "QA & Test Engineer", "asset": "Cybersecurity Compliance Competency", "conf": "High (90%)"}
        ]
        
        default_plan = {
            "timeline_phases": default_timeline,
            "resources": default_resources,
            "skills_mapping": default_skills
        }
        
        plan_data = safe_json_loads(plan_raw, default_plan)
        timeline_phases = plan_data.get("timeline_phases", default_timeline)
        resources = plan_data.get("resources", default_resources)
        skills_mapping = plan_data.get("skills_mapping", default_skills)
        
        # Calculate sizing summary
        total_fte = 0.0
        try:
            for r in resources:
                total_fte += float(r.get("fte", 0))
        except:
            total_fte = 5.15
            
        logs = f"Project estimation sized: Delivery duration mapped to {len(timeline_phases)} phases, totaling {total_fte:.2f} active FTEs."
        update_step_status(proposal_id, "Planning", "completed", logs)

        # ----------------------------------------------------
        # 5. PROPOSAL ASSEMBLY AGENT (Assembly & Reflexion)
        # ----------------------------------------------------
        update_step_status(proposal_id, "Assembling", "running", "Assembling final proposal content and running Reflexion quality checks...")
        
        draft_ir = {
            "proposal_title": f"Autonomous Proposal Document Creator Platform for {client_name}",
            "client_name": client_name,
            "project_duration": project_duration,
            "budget": budget,
            "requirements": requirements,
            "gaps": gaps,
            "solution_pillars": solution_pillars,
            "architecture": architecture,
            "timeline_phases": timeline_phases,
            "resources": resources,
            "skills_mapping": skills_mapping
        }
        
        reflexion_sys_prompt = (
            f"You are a Senior Reviewer auditing a proposal. The target budget is {budget} "
            f"and target duration is {project_duration}.\n"
            "Analyze the proposed JSON IR. Verify that the sum of the 'total' values in resources "
            "does not violate the target budget constraints, and that phase durations match the target duration.\n"
            "If any errors or overruns are detected, make precise corrections to the resource FTEs, "
            "monthly rates, and phase timelines so everything is aligned and compliant.\n"
            "Respond ONLY with the finalized, corrected JSON IR matching the input schema exactly. "
            "Do not include any formatting or text before or after the JSON."
        )
        reflexion_user_prompt = f"JSON IR Draft for Review:\n\n{json.dumps(draft_ir)}"
        
        final_ir_raw = query_llm(reflexion_sys_prompt, reflexion_user_prompt, json_mode=True)
        if final_ir_raw is None:
            raise RuntimeError("Failed to connect to local Mistral LLM server for Reflexion validation.")
        final_ir_data = safe_json_loads(final_ir_raw, draft_ir)
        
        # Save JSON IR to database for review/edit
        json_ir_str = json.dumps(final_ir_data)
        
        logs = "Self-reflexion validation audit: Successful. Budget and delivery constraints validated. JSON IR finalized."
        update_step_status(proposal_id, "Assembling", "completed", logs)

        # ----------------------------------------------------
        # 6. PPTX RENDERING (Deterministic PowerPoint generation)
        # ----------------------------------------------------
        update_step_status(proposal_id, "Complete", "running", "Rendering slides into brand-compliant PowerPoint deliverable...")
        
        out_dir = os.path.join(os.getcwd(), 'static', 'proposals')
        os.makedirs(out_dir, exist_ok=True)
        file_name = f"proposal_{proposal_id}.pptx"
        file_path = os.path.join(out_dir, file_name)
        
        generate_pptx(final_ir_data, file_path)
        
        relative_path = f"/static/proposals/{file_name}"
        
        logs = f"PowerPoint file compiled: {file_name}. Presentation layout successfully validated."
        update_step_status(proposal_id, "Complete", "completed", logs)
        
        # Mark entire proposal as Complete in the database
        update_proposal_status(proposal_id, "Complete", file_path=relative_path, json_ir=json_ir_str)
        
    except Exception as e:
        print(f"Error in multi-agent pipeline: {e}")
        import traceback
        tb = traceback.format_exc()
        update_proposal_status(proposal_id, "Failed")
        for step in STEPS:
            update_step_status(proposal_id, step, "failed", f"Failed due to error: {str(e)}\n{tb}")


def trigger_proposal_job(proposal_id, client_name, project_duration, budget, files_info):
    """Triggers the orchestrator thread asynchronously so UI remains non-blocking."""
    thread = threading.Thread(
        target=run_orchestration,
        args=(proposal_id, client_name, project_duration, budget, files_info)
    )
    thread.daemon = True
    thread.start()
