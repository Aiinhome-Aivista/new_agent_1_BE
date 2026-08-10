import os
import uuid
import json
from flask import request, send_file, jsonify
from database.db_connection import get_db_connection
from agents.orchestrator import trigger_proposal_job, STEPS, update_step_status
from utils.pptx_generator import generate_pptx
from utils.api_response import success_response, error_response

def format_datetime(val):
    if not val:
        return ""
    if isinstance(val, str):
        return val
    try:
        return val.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(val)

def generate_question():
    try:
        data = request.get_json()
        context = data.get('context', {})
        history = data.get('history', [])
        question_index = data.get('questionIndex', 1)
        
        system_prompt = f"""You are an intelligent proposal scoping assistant.
Your task is to ask the user a relevant, single follow-up question to gather more context about their project proposal.
The user is at question {question_index} out of 10.

CRITICAL INSTRUCTIONS:
1. You MUST ask a completely DIFFERENT question from the ones in the Q&A history.
2. Analyze the provided Context and Q&A history to deeply understand what critical information is still missing.
3. Determine the most important missing details needed to scope the project effectively and create a comprehensive PPT presentation (e.g., specific goals, tech stack preferences, success metrics, constraints, target audience, key deliverables).
4. Ask a highly targeted and precise question to obtain this specific missing information. Do NOT ask generic questions like "Could you provide more context?".
5. Keep the question very concise (1 sentence max).

Return your response strictly as a JSON object:
{{
    "question": "The question text here"
}}
"""
        
        history_text = ""
        for idx, qa in enumerate(history):
            history_text += f"Q{idx+1}: {qa.get('question')}\nA: {qa.get('answer')}\n\n"
            
        user_prompt = f"""
Current Context:
Client Name: {context.get('clientName', 'N/A')}
Project Duration: {context.get('projectDuration', 'N/A')}
Budget: {context.get('budget', 'N/A')}
Requirements Summary: {str(context.get('requirementsText', 'N/A'))[:500]}

Previous Q&A History:
{history_text if history_text else "None so far."}

Generate the next question to ask the user.
"""
        
        from utils.llm_client import query_llm, safe_json_loads
        res_str = query_llm(system_prompt, user_prompt, temperature=0.6, max_tokens=150)
        
        res_json = safe_json_loads(res_str, {"question": "Based on your requirements, what is the primary business outcome you are expecting?"})
        
        # If the LLM returned a completely empty question, use a dynamic-sounding default
        if not res_json.get("question") or len(res_json.get("question", "")) < 5:
            res_json["question"] = "What are the most critical success factors for this project?"
        
        return jsonify({"success": True, "data": res_json})
    except Exception as e:
        print(f"Error generating question: {e}")
        return jsonify({"success": False, "data": {"question": "Could you elaborate on the technical constraints for this project?"}}), 500

def upload_proposal():
    try:
        client_name = request.form.get("client_name")
        project_duration = request.form.get("project_duration")
        budget = request.form.get("budget")
        requirements_text = request.form.get("requirements_text")
        additional_context = request.form.get("additional_context")
        
        if not client_name or client_name.strip() == "":
            client_name = "Extracting Client Name..."
        if not project_duration or project_duration.strip() == "":
            project_duration = "Extracting..."
        if not budget or budget.strip() == "":
            budget = "Extracting..."
            
        # Parse files if any
        uploaded_files = []
        files = request.files.getlist("files")
        
        # Save files to temp upload directory
        upload_dir = os.path.join(os.getcwd(), 'static', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        for file in files:
            if file.filename:
                safe_name = f"{uuid.uuid4()}_{file.filename}"
                save_path = os.path.join(upload_dir, safe_name)
                file.save(save_path)
                
                # Extract text for validation
                from utils.doc_extractor import extract_text
                extracted_text = extract_text(save_path)
                
                # Document Validation
                from utils.llm_client import validate_document
                is_approved, res_json = validate_document(extracted_text)
                if not is_approved:
                    # Remove current file
                    if os.path.exists(save_path):
                        os.remove(save_path)
                    # Clean up other files uploaded in this request
                    for uf in uploaded_files:
                        if os.path.exists(uf["saved_path"]):
                            os.remove(uf["saved_path"])
                    from flask import jsonify
                    return jsonify(res_json), 400
                
                uploaded_files.append({
                    "original_name": file.filename,
                    "saved_path": save_path
                })
                
        # Parse case study files if any
        uploaded_case_study_files = []
        case_study_files = request.files.getlist("case_study_files")
        for file in case_study_files:
            if file.filename:
                safe_name = f"{uuid.uuid4()}_{file.filename}"
                save_path = os.path.join(upload_dir, safe_name)
                file.save(save_path)
                
                # Extract text for validation
                from utils.doc_extractor import extract_text
                extracted_text = extract_text(save_path)
                
                # Document Validation
                from utils.llm_client import validate_document
                is_approved, res_json = validate_document(extracted_text)
                if not is_approved:
                    # Remove current file
                    if os.path.exists(save_path):
                        os.remove(save_path)
                    # Clean up other files uploaded in this request
                    for uf in uploaded_files:
                        if os.path.exists(uf["saved_path"]):
                            os.remove(uf["saved_path"])
                    for uf in uploaded_case_study_files:
                        if os.path.exists(uf["saved_path"]):
                            os.remove(uf["saved_path"])
                    from flask import jsonify
                    return jsonify(res_json), 400
                
                uploaded_case_study_files.append({
                    "original_name": file.filename,
                    "saved_path": save_path
                })
                
        # Parse ppt template file if any
        ppt_template_path = None
        ppt_template_file = request.files.get("ppt_template")
        if ppt_template_file and ppt_template_file.filename:
            safe_name = f"{uuid.uuid4()}_{ppt_template_file.filename}"
            save_path = os.path.join(upload_dir, safe_name)
            ppt_template_file.save(save_path)
            ppt_template_path = save_path
        
        proposal_id = str(uuid.uuid4())[:8] # Short unique ID
        
        # Save to main proposals table
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if there is an active proposal
        cursor.execute("SELECT COUNT(*) FROM proposals WHERE status IN ('Ingesting', 'Analyzing', 'Designing', 'Planning', 'Assembling', 'WaitingForRateConfirmation')")
        active_count = cursor.fetchone()[0]
        status = "Queued" if active_count > 0 else "Ingesting"
 
        cursor.execute(
            "INSERT INTO proposals (id, client_name, project_duration, budget, status, files_info, requirements_text, case_study_files, ppt_template_file, additional_context) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (proposal_id, client_name, project_duration, budget, status, json.dumps(uploaded_files), requirements_text, json.dumps(uploaded_case_study_files), ppt_template_path, additional_context)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        if status == "Ingesting":
            # Start async agent job
            trigger_proposal_job(
                proposal_id=proposal_id,
                client_name=client_name,
                project_duration=project_duration,
                budget=budget,
                files_info=uploaded_files,
                requirements_text=requirements_text,
                case_study_files=uploaded_case_study_files,
                ppt_template_path=ppt_template_path
            )
            msg = "Proposal generation job triggered successfully"
        else:
            msg = "Proposal added to queue"

        return success_response({
            "message": msg,
            "proposal_id": proposal_id
        }, status_code=202)
        
    except Exception as e:
        return error_response(f"Failed to upload and start job: {str(e)}", status_code=500)

def get_proposals_list():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, client_name, project_duration, budget, status, generated_file_path, created_at FROM proposals ORDER BY created_at DESC")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Convert date to string
        for row in rows:
            if row.get("created_at"):
                row["created_at"] = format_datetime(row["created_at"])
                
        return success_response(rows)
    except Exception as e:
        # Fallback offline support
        return success_response([])

def get_proposal_status(proposal_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Fetch proposal details
        cursor.execute("SELECT * FROM proposals WHERE id = %s", (proposal_id,))
        proposal = cursor.fetchone()
        
        if not proposal:
            cursor.close()
            conn.close()
            return error_response("Proposal not found", status_code=404)
            
        # Fetch steps details
        cursor.execute("SELECT step_name, status, log_message, updated_at FROM proposal_steps WHERE proposal_id = %s ORDER BY id ASC", (proposal_id,))
        steps = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Formatting dates
        if proposal.get("created_at"):
            proposal["created_at"] = format_datetime(proposal["created_at"])
            
        formatted_steps = []
        for step in steps:
            if step.get("updated_at"):
                step["updated_at"] = format_datetime(step["updated_at"])
            formatted_steps.append(step)
            
        # Parse JSON IR if completed
        structured_ir = None
        if proposal.get("structured_json_ir"):
            try:
                structured_ir = json.loads(proposal["structured_json_ir"])
            except:
                pass
                
        return success_response({
            "proposal": proposal,
            "steps": formatted_steps,
            "structured_ir": structured_ir
        })
        
    except Exception as e:
        return error_response(f"Error retrieving job status: {str(e)}", status_code=500)


def pause_proposal_job(proposal_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE proposals SET status = 'Paused' WHERE id = %s", (proposal_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        process_next_in_queue()
        return success_response({"message": "Proposal paused successfully"})
    except Exception as e:
        return error_response(f"Failed to pause: {str(e)}", status_code=500)

def cancel_proposal_job(proposal_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE proposals SET status = 'Cancelled' WHERE id = %s", (proposal_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        process_next_in_queue()
        return success_response({"message": "Proposal cancelled successfully"})
    except Exception as e:
        return error_response(f"Failed to cancel: {str(e)}", status_code=500)

def process_next_in_queue():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True) if hasattr(conn.cursor, 'dictionary') else conn.cursor()
        # Check if anything is running
        cursor.execute("SELECT COUNT(*) as cnt FROM proposals WHERE status IN ('Ingesting', 'Analyzing', 'Designing', 'Planning', 'Assembling', 'WaitingForRateConfirmation')")
        row = cursor.fetchone()
        active_count = row.get('cnt', 0) if isinstance(row, dict) else row[0]
        
        if active_count == 0:
            cursor.execute("SELECT id FROM proposals WHERE status = 'Queued' ORDER BY created_at ASC LIMIT 1")
            row = cursor.fetchone()
            if row:
                next_id = row.get('id') if isinstance(row, dict) else row[0]
                cursor.execute("UPDATE proposals SET status = 'Ingesting' WHERE id = %s", (next_id,))
                conn.commit()
                # Trigger it
                import threading
                threading.Thread(target=trigger_next_job_async, args=(next_id,)).start()
        
        cursor.close()
        conn.close()
    except Exception as e:
        print('Error processing next in queue:', e)

def trigger_next_job_async(proposal_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True) if hasattr(conn.cursor, 'dictionary') else conn.cursor()
        cursor.execute("SELECT client_name, project_duration, budget, files_info, requirements_text, case_study_files, ppt_template_file FROM proposals WHERE id = %s", (proposal_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if row:
            import json
            client_name = row.get('client_name') if isinstance(row, dict) else row[0]
            project_duration = row.get('project_duration') if isinstance(row, dict) else row[1]
            budget = row.get('budget') if isinstance(row, dict) else row[2]
            
            f_info = row.get('files_info') if isinstance(row, dict) else row[3]
            files_info = json.loads(f_info) if f_info else []
            
            r_text = row.get('requirements_text') if isinstance(row, dict) else row[4]
            
            c_info = row.get('case_study_files') if isinstance(row, dict) else row[5]
            case_study_files = json.loads(c_info) if c_info else []
            
            p_temp = row.get('ppt_template_file') if isinstance(row, dict) else row[6]
            
            trigger_proposal_job(
                proposal_id=proposal_id,
                client_name=client_name,
                project_duration=project_duration,
                budget=budget,
                files_info=files_info,
                requirements_text=r_text,
                case_study_files=case_study_files,
                ppt_template_path=p_temp
            )
    except Exception as e:
        print('Error in trigger_next_job_async:', e)

def resume_proposal_job(proposal_id):
    """Resumes a failed or pending proposal orchestration."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True) if hasattr(conn.cursor, 'dictionary') else conn.cursor()
        cursor.execute("SELECT client_name, project_duration, budget, files_info, requirements_text, case_study_files FROM proposals WHERE id = %s", (proposal_id,))
        row = cursor.fetchone()
        
        if not row:
            return error_response("Proposal not found", status_code=404)
            
        client_name = row.get("client_name") if isinstance(row, dict) else row[0]
        project_duration = row.get("project_duration") if isinstance(row, dict) else row[1]
        budget = row.get("budget") if isinstance(row, dict) else row[2]
        files_info_str = row.get("files_info") if isinstance(row, dict) else row[3]
        requirements_text = row.get("requirements_text") if isinstance(row, dict) else row[4]
        case_study_files_str = row.get("case_study_files") if isinstance(row, dict) else row[5]

        files_info = json.loads(files_info_str) if files_info_str else []
        case_study_files = json.loads(case_study_files_str) if case_study_files_str else []

        # Assuming we need to import run_orchestration here or it's already imported
        # Wait, trigger_proposal_job triggers the thread, we should use a similar trigger_resume_job
        from agents.orchestrator import trigger_resume_job
        # Get ppt_template_file from DB
        cursor = conn.cursor()
        cursor.execute("SELECT ppt_template_file FROM proposals WHERE id = %s", (proposal_id,))
        pt_row = cursor.fetchone()
        ppt_template_path = pt_row[0] if pt_row else None
        cursor.close()

        # Pause any active proposals
        cursor = conn.cursor()
        cursor.execute("UPDATE proposals SET status = 'Paused' WHERE status IN ('Ingesting', 'Analyzing', 'Designing', 'Planning', 'Assembling', 'WaitingForRateConfirmation') AND id != %s", (proposal_id,))
        cursor.execute("UPDATE proposals SET status = 'Ingesting' WHERE id = %s", (proposal_id,))
        conn.commit()
        cursor.close()
        conn.close()

        trigger_resume_job(proposal_id, client_name, project_duration, budget, files_info, requirements_text, case_study_files, ppt_template_path)
        
        return success_response({"message": "Job resumed successfully.", "proposal_id": proposal_id})
    except Exception as e:
        return error_response(f"Error resuming job: {str(e)}", status_code=500)

def edit_proposal_ir(proposal_id):
    """Saves updated JSON IR, then deterministically regenerates the PPTX file (HITL workflow)."""
    try:
        new_ir_data = request.get_json()
        if not new_ir_data:
            return error_response("JSON body data is required", status_code=400)
            
        # Regenerate pptx file
        out_dir = os.path.join(os.getcwd(), 'static', 'proposals')
        file_name = f"proposal_{proposal_id}.pptx"
        file_path = os.path.join(out_dir, file_name)
        
        # Render the updated PPTX
        generate_pptx(new_ir_data, file_path)
        
        # Update MySQL
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE proposals SET structured_json_ir = %s, generated_file_path = %s WHERE id = %s",
            (json.dumps(new_ir_data), f"/static/proposals/{file_name}", proposal_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        return success_response({
            "message": "Proposal document updated and regenerated successfully",
            "file_path": f"/static/proposals/{file_name}",
            "structured_ir": new_ir_data
        })
        
    except Exception as e:
        return error_response(f"Failed to edit and update proposal: {str(e)}", status_code=500)

def download_proposal_pptx(proposal_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT generated_file_path FROM proposals WHERE id = %s", (proposal_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not row or not row.get("generated_file_path"):
            return error_response("Proposal file not generated yet", status_code=400)
            
        relative_path = row["generated_file_path"]
        # Convert relative URL /static/proposals/... to local absolute filepath
        filename = os.path.basename(relative_path)
        absolute_path = os.path.join(os.getcwd(), 'static', 'proposals', filename)
        
        if os.path.exists(absolute_path):
            return send_file(absolute_path, as_attachment=True, download_name=filename)
        else:
            return error_response(f"File not found on disk at: {absolute_path}", status_code=404)
            
    except Exception as e:
        return error_response(f"Failed to send file: {str(e)}", status_code=500)

def transition_proposal_status(proposal_id):
    """Enforce a strict role-based state machine for proposal business workflow.
    
    Allowed transitions:
      Complete        → Draft           (presales, bidmanager, admin)
      Draft           → DeliveryReview  (presales, bidmanager, admin)
      DeliveryReview  → PartnerReview   (delivery, admin)
      PartnerReview   → Approved        (partner, admin)
      PartnerReview   → Draft           (partner, admin — Reject/back for revision)
      Approved        → Published       (partner, admin)
    """
    try:
        data = request.get_json() or {}
        new_status = data.get("status")
        user_role = data.get("user_role", "").strip()
        
        if not new_status:
            return error_response("Status is required", status_code=400)
        if not user_role:
            return error_response("user_role is required", status_code=400)
            
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT status FROM proposals WHERE id = %s", (proposal_id,))
        prop = cursor.fetchone()
        
        if not prop:
            cursor.close()
            conn.close()
            return error_response("Proposal not found", status_code=404)
            
        current_status = prop["status"]
        
        # -------------------------------------------------------
        # TRANSITION STATE MACHINE
        # Keys: (from_status, to_status) → allowed_roles tuple
        # -------------------------------------------------------
        ALLOWED_TRANSITIONS = {
            ("Complete",        "Approved"):       ("presales", "bidmanager", "admin", "partner", "delivery"),
            ("Complete",        "Rejected"):       ("presales", "bidmanager", "admin", "partner", "delivery"),
            ("Rejected",        "Approved"):       ("presales", "bidmanager", "admin", "partner", "delivery"),
            ("Approved",        "Published"):      ("presales", "bidmanager", "admin", "partner", "delivery"),
        }
        
        transition_key = (current_status, new_status)
        allowed_roles_for_transition = ALLOWED_TRANSITIONS.get(transition_key)
        
        if allowed_roles_for_transition is None:
            cursor.close()
            conn.close()
            return error_response(f"Transition from '{current_status}' to '{new_status}' is not a valid workflow step.", status_code=400)
        
        if user_role not in allowed_roles_for_transition:
            cursor.close()
            conn.close()
            return error_response(f"Role '{user_role}' cannot transition from '{current_status}' to '{new_status}'. Allowed roles: {list(allowed_roles_for_transition)}", status_code=403)
            
        # Perform status update, record who made the transition and when
        cursor.execute(
            "UPDATE proposals SET status = %s, submitted_by_role = %s, last_transitioned_at = CURRENT_TIMESTAMP WHERE id = %s",
            (new_status, user_role, proposal_id)
        )
        
        # Add human-readable log entry to proposal_steps for audit trail
        action_labels = {
            ("Complete",       "Approved"):      "Proposal APPROVED",
            ("Complete",       "Rejected"):      "Proposal REJECTED — returned for revision",
            ("Rejected",       "Approved"):      "Proposal APPROVED",
            ("Approved",       "Published"):     "Proposal PUBLISHED and finalized",
        }
        log_msg = action_labels.get(transition_key, f"Status moved from {current_status} to {new_status}")
        
        cursor.execute(
            "INSERT INTO proposal_steps (proposal_id, step_name, status, log_message) VALUES (%s, %s, %s, %s)",
            (proposal_id, new_status, "completed", f"[{user_role.upper()}] {log_msg}")
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        # Trigger next in queue if available
        process_next_in_queue()
        
        return success_response({"message": f"Proposal successfully transitioned to '{new_status}'"})
        
    except Exception as e:
        return error_response(str(e), status_code=500)


def get_users():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, username, role, created_at FROM users ORDER BY username")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        for r in rows:
            if r.get("created_at"):
                r["created_at"] = format_datetime(r["created_at"])
        return success_response(rows)
    except Exception as e:
        return error_response(str(e), status_code=500)

def change_user_role():
    try:
        data = request.get_json() or {}
        username = data.get("username")
        new_role = data.get("role")
        
        if not username or not new_role:
            return error_response("Username and role are required", status_code=400)
            
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET role = %s WHERE username = %s", (new_role, username))
        conn.commit()
        cursor.close()
        conn.close()
        return success_response({"message": f"User {username} role updated to {new_role}"})
    except Exception as e:
        return error_response(str(e), status_code=500)

def get_admin_config():
    try:
        from database.arango_client import arango_client
        arango_status = "Online" if arango_client.is_connected else "Offline"
        
        conn = get_db_connection()
        mysql_status = "Online" if conn.mysql_conn else "Offline (Using Local SQLite Mirror)"
        conn.close()
        
        config_data = {
            "mysql_status": mysql_status,
            "arango_status": arango_status,
            "arango_url": os.getenv("ARANGO_URL"),
            "arango_db": os.getenv("ARANGO_DB"),
            "mistral_url": os.getenv("MISTRAL_LOCAL_URL"),
            "active_ai_model": os.getenv("MISTRAL_LOCAL_MODEL", "mistral-small:24b"),
        }
        return success_response(config_data)
    except Exception as e:
        return error_response(str(e), status_code=500)

def get_all_audit_logs():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT s.proposal_id, p.client_name, s.step_name, s.status, s.log_message, s.updated_at 
            FROM proposal_steps s 
            JOIN proposals p ON s.proposal_id = p.id 
            ORDER BY s.updated_at DESC
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        for r in rows:
            if r.get("updated_at"):
                r["updated_at"] = format_datetime(r["updated_at"])
        return success_response(rows)
    except Exception as e:
        return error_response(str(e), status_code=500)

def retry_proposal_job(proposal_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT client_name, project_duration, budget FROM proposals WHERE id = %s", (proposal_id,))
        prop = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not prop:
            return error_response("Proposal not found", status_code=404)
            
        client_name = prop["client_name"]
        project_duration = prop["project_duration"]
        budget = prop["budget"]
        
        # Reset steps
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM proposal_steps WHERE proposal_id = %s", (proposal_id,))
        cursor.execute("UPDATE proposals SET status = %s WHERE id = %s", ("Ingesting", proposal_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        # Trigger job async
        # In a real retry, we would fetch ppt_template_file from db as well, but for now we skip or fetch it
        cursor = conn.cursor()
        cursor.execute("SELECT ppt_template_file FROM proposals WHERE id = %s", (proposal_id,))
        pt_row = cursor.fetchone()
        ppt_template_path = pt_row[0] if pt_row else None
        cursor.close()
        
        trigger_proposal_job(
            proposal_id=proposal_id,
            client_name=client_name,
            project_duration=project_duration,
            budget=budget,
            files_info=[], # Clean retry
            ppt_template_path=ppt_template_path
        )
        return success_response({"message": f"Job retry triggered for proposal {proposal_id}"})
    except Exception as e:
        return error_response(str(e), status_code=500)

def get_tech_options():
    try:
        from utils.pricing_kb import get_technology_options
        return success_response(get_technology_options())
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(str(e), status_code=500)

def calculate_budget():
    try:
        data = request.get_json() or {}
        ui_tech = data.get("ui_tech", "")
        backend_tech = data.get("backend_tech", "")
        db_tech = data.get("db_tech", "")
        
        from utils.pricing_kb import calculate_budget as calc_budget
        budget_info = calc_budget(ui_tech, backend_tech, db_tech)
        return success_response(budget_info)
    except Exception as e:
        return error_response(str(e), status_code=500)

def resume_proposal(proposal_id):
    try:
        data = request.get_json() or {}
        ui_tech = data.get("ui_tech", "React")
        backend_tech = data.get("backend_tech", "Flask")
        db_tech = data.get("db_tech", "MySQL")
        final_budget = data.get("formatted_budget", "$250,000")
        selected_rag = data.get("selected_rag", "")
        selected_guardrail = data.get("selected_guardrail", "")
        selected_action_engine = data.get("selected_action_engine", "")
        
        # Synchronously update status and budget to prevent race conditions on the frontend
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE proposals SET status = 'Designing', budget = %s WHERE id = %s",
            (final_budget, proposal_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        from agents.orchestrator import resume_orchestration_phase2
        import threading
        
        thread = threading.Thread(
            target=resume_orchestration_phase2,
            args=(proposal_id, ui_tech, backend_tech, db_tech, final_budget, selected_rag, selected_guardrail, selected_action_engine)
        )
        thread.daemon = True
        thread.start()
        
        return success_response({"message": f"Resumed orchestration for {proposal_id} with new budget {final_budget}"})
    except Exception as e:
        return error_response(str(e), status_code=500)

def update_ai_model():
    try:
        data = request.get_json() or {}
        model_name = data.get("model_name")
        if not model_name:
            return error_response("Model name is required", status_code=400)
            
        # Update environment variable
        os.environ["MISTRAL_LOCAL_MODEL"] = model_name
        import utils.llm_client
        import database.vector_client
        utils.llm_client.MISTRAL_LOCAL_MODEL = model_name
        database.vector_client.MISTRAL_LOCAL_MODEL = model_name
        
        return success_response({"message": f"Active AI Model updated to {model_name}"})
    except Exception as e:
        return error_response(str(e), status_code=500)

def resume_proposal_rate(proposal_id):
    try:
        from flask import request
        data = request.get_json() or {}
        updated_resources = data.get("resources", [])
        
        from database.db_connection import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE proposals SET status = 'Assembling' WHERE id = %s",
            (proposal_id,)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        from agents.orchestrator import resume_orchestration_phase3
        import threading
        
        thread = threading.Thread(
            target=resume_orchestration_phase3,
            args=(proposal_id, updated_resources)
        )
        thread.daemon = True
        thread.start()
        
        return success_response({"message": f"Resumed orchestration phase 3 for {proposal_id}"})
    except Exception as e:
        return error_response(str(e), status_code=500)
