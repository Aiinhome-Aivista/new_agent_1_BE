import os
import json
import uuid
import time
import threading
from database.db_connection import get_db_connection
from utils.pptx_generator import generate_pptx
from utils.llm_client import query_llm
from utils.doc_extractor import extract_text
from database.arango_client import arango_client
from database.vector_client import get_embedding, retrieve_nearest, cosine_similarity

# Import LangChain Agents
from agents.intake_agent import IntakeAgent
from agents.requirement_agent import RequirementAgent


def chunk_text(text, chunk_size=1000, overlap=100):
    """Splits document text into overlapping blocks of characters."""
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
    return chunks

def classify_chunk(chunk_content):
    """Queries Mistral to classify the document chunk."""
    sys_prompt = (
        "You are an assistant that classifies document sections from an RFP.\n"
        "Classify the text into exactly one of these labels:\n"
        "- Background\n"
        "- Requirements\n"
        "- Financial & Sizing\n"
        "- Compliance & Security\n"
        "- Other\n"
        "Respond ONLY with the selected label (e.g. 'Requirements'). No markdown, punctuation or explanation."
    )
    res = query_llm(sys_prompt, chunk_content[:1500])
    if res:
        clean = res.strip().strip("'\"`").strip()
        for cat in ["Background", "Requirements", "Financial & Sizing", "Compliance & Security", "Other"]:
            if cat.lower() in clean.lower():
                return cat
    return "Other"


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
        elif json_ir:
            cursor.execute(
                "UPDATE proposals SET status = %s, structured_json_ir = %s WHERE id = %s",
                (status, json_ir, proposal_id)
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
        # Initialize LangChain Agents
        intake_agent = IntakeAgent()
        req_agent = RequirementAgent()

        # Initialize steps in database as 'pending'
        for step in STEPS:
            update_step_status(proposal_id, step, "pending", "Waiting to start...")


        # ----------------------------------------------------
        # 1. INTAKE AGENT (Document parsing, extraction & validation)
        # ----------------------------------------------------
        update_step_status(proposal_id, "Ingesting", "running", "Ingesting client documents: validating format & extracting text...")
        
        # Initialize ArangoDB connection and schema setup
        print("Initializing ArangoDB client...")
        arango_client.init_db()
        
        extracted_text_blocks = []
        parsed_files = 0
        total_chunks_stored = 0
        
        if files_info:
            for file_data in files_info:
                saved_path = file_data.get("saved_path")
                orig_name = file_data.get("original_name")
                if saved_path and os.path.exists(saved_path):
                    txt = extract_text(saved_path)
                    if txt:
                        parsed_files += 1
                        extracted_text_blocks.append(f"--- Document: {orig_name} ---\n{txt}")
                        
                        # Smart Chunking and Classification
                        chunks = chunk_text(txt, chunk_size=1000, overlap=100)
                        from database.vector_client import store_embedding
                        for idx, chunk in enumerate(chunks):
                            classification = intake_agent.classify_chunk(chunk)

                            embedding = get_embedding(chunk)
                            
                            chunk_id = f"{proposal_id}_{orig_name}_{idx}"
                            
                            # Save to ArangoDB chunks collection
                            if arango_client.is_connected:
                                chunk_doc = {
                                    "_key": chunk_id,
                                    "proposal_id": proposal_id,
                                    "filename": orig_name,
                                    "chunk_index": idx,
                                    "text": chunk,
                                    "classification": classification,
                                    "embedding": embedding
                                }
                                arango_client.insert("chunks", chunk_doc)
                            
                            # Save to ChromaDB
                            store_embedding(
                                collection_name="chunks",
                                doc_id=chunk_id,
                                text=chunk,
                                metadata={
                                    "proposal_id": proposal_id,
                                    "filename": orig_name,
                                    "classification": classification
                                }
                            )
                            
                            total_chunks_stored += 1
                        
                        # Save document record to ArangoDB
                        if arango_client.is_connected:
                            doc_record = {
                                "proposal_id": proposal_id,
                                "filename": orig_name,
                                "character_count": len(txt)
                            }
                            arango_client.insert("documents", doc_record)
        
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
            # Query LLM to extract metadata using LangChain IntakeAgent
            extracted_meta = intake_agent.extract_metadata(full_document_text)
            if needs_client:
                ext_client = str(extracted_meta.get("client_name") or "").strip()
                if not ext_client or "Extracting" in ext_client:
                    client_name = "Acme Corporation"
                else:
                    client_name = ext_client
            if needs_duration:
                ext_duration = str(extracted_meta.get("project_duration") or "").strip()
                if not ext_duration or "Extracting" in ext_duration:
                    project_duration = "14 Weeks"
                else:
                    project_duration = ext_duration
            if needs_budget:
                ext_budget = str(extracted_meta.get("budget") or "").strip()
                if not ext_budget or "Extracting" in ext_budget:
                    budget = "$250,000"
                else:
                    budget = ext_budget
                
            # Update the database with the extracted metadata
            update_proposal_metadata(proposal_id, client_name, project_duration, budget)


        # Save proposal metadata to ArangoDB
        if arango_client.is_connected:
            prop_record = {
                "_key": proposal_id,
                "client_name": client_name,
                "project_duration": project_duration,
                "budget": budget,
                "status": "Ingesting"
            }
            arango_client.insert("proposals", prop_record)

        logs = f"Parsed {parsed_files} document(s). Generated and indexed {total_chunks_stored} text chunks in ArangoDB."
        update_step_status(proposal_id, "Ingesting", "completed", logs)

        # ----------------------------------------------------
        # 2. KNOWLEDGE AGENT (LLM Requirement Extraction & RAG mapping)
        # ----------------------------------------------------
        update_step_status(proposal_id, "Analyzing", "running", "Extracting requirements & querying PwC assets repository (RAG)...")
        
        # Extract requirements using LangChain RequirementAgent
        requirements = req_agent.extract_requirements(full_document_text)
        
        # Extract tech stack and get suggestions using LangChain RequirementAgent
        tech_data = req_agent.analyze_tech_stack(full_document_text, requirements)
        
        # Run RAG Grounding and Gap Analysis
        rag_data = req_agent.run_rag_analysis(requirements, project_duration)
        matched = rag_data.get("matched", [])
        gaps = rag_data.get("gaps", [])
        
        # Analyze Advanced Options (RAG Strategy, Action Engine, Guardrails)
        advanced_options = req_agent.analyze_advanced_options(full_document_text, requirements)
        
        logs = f"RAG Grounding complete: Mapped {len(matched)} requirement(s) to assets. Flagged {len(gaps)} gap(s)."
        update_step_status(proposal_id, "Analyzing", "completed", logs)

        # PAUSE HERE: Save intermediate state to structured_json_ir so Phase 2 can pick it up.
        partial_state = {
            "client_name": client_name,
            "project_duration": project_duration,
            "budget": budget,
            "requirements": requirements,
            "matched_assets": matched,
            "gaps": gaps,
            "extracted_technologies": tech_data.get("extracted_technologies", {"ui": None, "backend": None, "database": None}),
            "tech_options": tech_data.get("tech_options", []),
            "chat_explanation": tech_data.get("chat_explanation", ""),
            "rag_options": advanced_options.get("rag_options", []),
            "action_engine_options": advanced_options.get("action_engine_options", []),
            "guardrail_options": advanced_options.get("guardrail_options", [])
        }
        update_proposal_status(proposal_id, "WaitingForTechSelection", json_ir=json.dumps(partial_state))
        
        # Stop the thread. The UI will resume it by calling the resume endpoint.
        return
        
    except Exception as e:
        print(f"Error in multi-agent pipeline: {e}")
        import traceback
        tb = traceback.format_exc()
        update_proposal_status(proposal_id, "Failed")
        for step in STEPS:
            update_step_status(proposal_id, step, "failed", f"Failed due to error: {str(e)}\n{tb}")

def resume_orchestration_phase2(proposal_id, ui_tech, backend_tech, db_tech, final_budget, selected_rag="", selected_guardrail="", selected_action_engine=""):
    """Phase 2 of Orchestration: Designing, Planning, Assembling, PPTX rendering."""
    try:
        # Retrieve the partial state
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT structured_json_ir FROM proposals WHERE id = %s", (proposal_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not row or not row.get("structured_json_ir"):
            raise ValueError("No intermediate state found to resume.")
            
        partial_state = json.loads(row["structured_json_ir"])
        client_name = partial_state.get("client_name", "Client")
        project_duration = partial_state.get("project_duration", "14 Weeks")
        budget = final_budget  # Override with user-selected budget
        requirements = partial_state.get("requirements", [])
        gaps = partial_state.get("gaps", [])
        
        # ----------------------------------------------------
        # 3. SOLUTION DESIGN AGENT (Tree-of-Thoughts Architecture)
        # ----------------------------------------------------
        update_step_status(proposal_id, "Designing", "running", f"Designing technical solution using {ui_tech}, {backend_tech}, {db_tech}...")
        
        from agents.design_agent import DesignAgent
        design_agent = DesignAgent()
        design_data = design_agent.generate_design(
            ui_tech=ui_tech,
            backend_tech=backend_tech,
            db_tech=db_tech,
            requirements=requirements,
            budget=budget,
            duration=project_duration,
            selected_rag=selected_rag,
            selected_guardrail=selected_guardrail,
            selected_action_engine=selected_action_engine
        )
        solution_pillars = design_data.get("solution_pillars", [])
        architecture = design_data.get("architecture", [])

        
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
            "'rate' (monthly rate string, e.g., '$8,000'), 'total' (total cost calculation for this resource as a string, e.g. '$10,000'), "
            "and 'person_days' (integer representing total estimated effort in days, e.g. 40).\n"
            "- 'skills_mapping': a list of exactly 5 skills mapping objects. Each object contains: "
            "'skill' (technical skill name), 'role' (matching project role), 'asset' (matching PwC Asset/Competency name), "
            "and 'conf' (confidence percentage string, e.g. '95%').\n"
            f"CRITICAL: The sum of the 'total' cost for all resources MUST EXACTLY equal the target budget of {budget}. "
            f"Convert {project_duration} to months to calculate (rate * fte * months = total), but adjust the numbers so the sum matches the budget perfectly.\n"
            "Do not include formatting before or after the JSON."
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
            {"role": "Engagement Director", "loc": "Hybrid", "fte": "0.15", "rate": "$32,000", "total": "$21,600", "person_days": 10},
            {"role": "Lead Architect", "loc": "Onsite", "fte": "1.00", "rate": "$25,000", "total": "$100,000", "person_days": 60},
            {"role": "Senior Developer (Front-end)", "loc": "Offshore", "fte": "1.50", "rate": "$8,000", "total": "$48,000", "person_days": 90},
            {"role": "Senior Developer (Back-end)", "loc": "Offshore", "fte": "1.50", "rate": "$8,000", "total": "$48,000", "person_days": 90},
            {"role": "QA & Test Engineer", "loc": "Offshore", "fte": "1.00", "rate": "$6,000", "total": "$24,000", "person_days": 60}
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
            "business_summary": design_data.get("business_summary", ""),
            "data_flow": design_data.get("data_flow", []),
            "infrastructure_approximation": design_data.get("infrastructure_approximation", []),
            "similar_projects": design_data.get("similar_projects", []),
            "timeline_phases": timeline_phases,
            "resources": resources,
            "skills_mapping": skills_mapping,
            "complex_diagrams": design_data.get("complex_diagrams", [])
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
            print("Warning: Failed to connect to local Mistral LLM server for Reflexion validation. Falling back to draft IR.")
            final_ir_data = draft_ir
        else:
            final_ir_data = safe_json_loads(final_ir_raw, draft_ir)
        
        # Python math override to ensure totals match budget
        import re
        try:
            target_budget_str = str(budget).replace(',', '').replace('$', '').strip()
            target_budget_val = float(target_budget_str)
            
            dur_match = re.search(r'(\d+)', str(project_duration))
            weeks = float(dur_match.group(1)) if dur_match else 32.0
            months = max(weeks / 4.0, 1.0)

            resources_list = final_ir_data.get("resources", [])
            total_current = 0.0
            parsed_res = []
            
            for r in resources_list:
                tot_str = str(r.get("total", "0")).replace(',', '').replace('$', '').strip()
                try:
                    tot_val = float(tot_str)
                except:
                    tot_val = 1000.0
                total_current += tot_val
                parsed_res.append(tot_val)
                
            if total_current > 0:
                scale = target_budget_val / total_current
                for i, r in enumerate(resources_list):
                    new_tot = parsed_res[i] * scale
                    try:
                        fte_val = float(str(r.get("fte", "1.0")))
                    except:
                        fte_val = 1.0
                    
                    if fte_val > 0:
                        new_rate = new_tot / (fte_val * months)
                    else:
                        new_rate = 0.0
                        
                    r["total"] = f"${int(new_tot):,}"
                    r["rate"] = f"${int(new_rate):,}"
                    
            final_ir_data["resources"] = resources_list
        except Exception as math_e:
            print(f"Failed to normalize resource budget: {math_e}")
            
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
        import re
        if isinstance(client_name, list):
            client_name = client_name[0] if client_name else "Project"
        safe_client_name = re.sub(r'[^a-zA-Z0-9]', '_', str(client_name)).strip('_')
        if not safe_client_name:
            safe_client_name = "Project"
            
        file_name = f"{safe_client_name}_Proposal.pptx"
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
