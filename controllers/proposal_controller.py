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
        project_duration = request.form.get("project_duration", "12 Weeks")
        budget = request.form.get("budget", "$200,000")
        
        if not client_name:
            return jsonify({"error": "Client name is required"}), 400
            
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
