import os
import uuid
import json
from flask import request, jsonify, send_file
from database.db_connection import get_db_connection
from agents.orchestrator import trigger_proposal_job, STEPS, update_step_status
from utils.pptx_generator import generate_pptx

def format_datetime(val):
    if not val:
        return ""
    if isinstance(val, str):
        return val
    try:
        return val.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(val)

def upload_proposal():
    try:
        client_name = request.form.get("client_name")
        project_duration = request.form.get("project_duration")
        budget = request.form.get("budget")
        
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
                uploaded_files.append({
                    "original_name": file.filename,
                    "saved_path": save_path
                })
        
        proposal_id = str(uuid.uuid4())[:8] # Short unique ID
        
        # Save to main proposals table
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO proposals (id, client_name, project_duration, budget, status) VALUES (%s, %s, %s, %s, %s)",
            (proposal_id, client_name, project_duration, budget, "Ingesting")
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        # Start async agent job
        trigger_proposal_job(
            proposal_id=proposal_id,
            client_name=client_name,
            project_duration=project_duration,
            budget=budget,
            files_info=uploaded_files
        )
        
        return jsonify({
            "message": "Proposal generation job triggered successfully",
            "proposal_id": proposal_id
        }), 202
        
    except Exception as e:
        return jsonify({"error": f"Failed to upload and start job: {str(e)}"}), 500

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
                
        return jsonify(rows), 200
    except Exception as e:
        # Fallback offline support
        return jsonify([]), 200

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
            return jsonify({"error": "Proposal not found"}), 404
            
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
                
        return jsonify({
            "proposal": proposal,
            "steps": formatted_steps,
            "structured_ir": structured_ir
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Error retrieving job status: {str(e)}"}), 500

def edit_proposal_ir(proposal_id):
    """Saves updated JSON IR, then deterministically regenerates the PPTX file (HITL workflow)."""
    try:
        new_ir_data = request.get_json()
        if not new_ir_data:
            return jsonify({"error": "JSON body data is required"}), 400
            
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
        
        return jsonify({
            "message": "Proposal document updated and regenerated successfully",
            "file_path": f"/static/proposals/{file_name}",
            "structured_ir": new_ir_data
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to edit and update proposal: {str(e)}"}), 500

def download_proposal_pptx(proposal_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT generated_file_path FROM proposals WHERE id = %s", (proposal_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not row or not row.get("generated_file_path"):
            return jsonify({"error": "Proposal file not generated yet"}), 400
            
        relative_path = row["generated_file_path"]
        # Convert relative URL /static/proposals/... to local absolute filepath
        filename = os.path.basename(relative_path)
        absolute_path = os.path.join(os.getcwd(), 'static', 'proposals', filename)
        
        if os.path.exists(absolute_path):
            return send_file(absolute_path, as_attachment=True, download_name=filename)
        else:
            return jsonify({"error": f"File not found on disk at: {absolute_path}"}), 404
            
    except Exception as e:
        return jsonify({"error": f"Failed to send file: {str(e)}"}), 500

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
            return jsonify({"error": "Status is required"}), 400
        if not user_role:
            return jsonify({"error": "user_role is required"}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT status FROM proposals WHERE id = %s", (proposal_id,))
        prop = cursor.fetchone()
        
        if not prop:
            cursor.close()
            conn.close()
            return jsonify({"error": "Proposal not found"}), 404
            
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
            return jsonify({
                "error": f"Transition from '{current_status}' to '{new_status}' is not a valid workflow step."
            }), 400
        
        if user_role not in allowed_roles_for_transition:
            cursor.close()
            conn.close()
            return jsonify({
                "error": f"Role '{user_role}' cannot transition from '{current_status}' to '{new_status}'. "
                         f"Allowed roles: {list(allowed_roles_for_transition)}"
            }), 403
            
        # Perform status update, record who made the transition and when
        cursor.execute(
            "UPDATE proposals SET status = %s, submitted_by_role = %s, last_transitioned_at = NOW() WHERE id = %s",
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
        
        return jsonify({"message": f"Proposal successfully transitioned to '{new_status}'"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
        return jsonify(rows), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def change_user_role():
    try:
        data = request.get_json() or {}
        username = data.get("username")
        new_role = data.get("role")
        
        if not username or not new_role:
            return jsonify({"error": "Username and role are required"}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET role = %s WHERE username = %s", (new_role, username))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": f"User {username} role updated to {new_role}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
        return jsonify(config_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
        return jsonify(rows), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def retry_proposal_job(proposal_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT client_name, project_duration, budget FROM proposals WHERE id = %s", (proposal_id,))
        prop = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not prop:
            return jsonify({"error": "Proposal not found"}), 404
            
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
        trigger_proposal_job(
            proposal_id=proposal_id,
            client_name=client_name,
            project_duration=project_duration,
            budget=budget,
            files_info=[] # Clean retry
        )
        return jsonify({"message": f"Job retry triggered for proposal {proposal_id}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_tech_options():
    try:
        from utils.pricing_kb import get_technology_options
        return jsonify(get_technology_options()), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

def calculate_budget():
    try:
        data = request.get_json() or {}
        ui_tech = data.get("ui_tech", "")
        backend_tech = data.get("backend_tech", "")
        db_tech = data.get("db_tech", "")
        
        from utils.pricing_kb import calculate_budget as calc_budget
        budget_info = calc_budget(ui_tech, backend_tech, db_tech)
        return jsonify(budget_info), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
        
        return jsonify({"message": f"Resumed orchestration for {proposal_id} with new budget {final_budget}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def update_ai_model():
    try:
        data = request.get_json() or {}
        model_name = data.get("model_name")
        if not model_name:
            return jsonify({"error": "Model name is required"}), 400
            
        # Update environment variable
        os.environ["MISTRAL_LOCAL_MODEL"] = model_name
        import utils.llm_client
        import database.vector_client
        utils.llm_client.MISTRAL_LOCAL_MODEL = model_name
        database.vector_client.MISTRAL_LOCAL_MODEL = model_name
        
        return jsonify({"message": f"Active AI Model updated to {model_name}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
